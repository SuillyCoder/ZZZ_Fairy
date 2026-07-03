import os, sys, ast, json, shutil, difflib, subprocess, requests

#Import from config file path 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OLLAMA_URL, MODEL_NAME, FAIRY_GROQ_API_KEY, GROQ_MODEL, BASE_DIR

#Groq model import
from groq import Groq
groq_client = Groq(api_key=FAIRY_GROQ_API_KEY)

# Set value for how many lines per chunk when a file can't be cleanly split by function/class
FALLBACK_CHUNK_LINES = 80

# Where backups go before any file gets overwritten
BACKUP_DIR = os.path.join(BASE_DIR, "code_backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


# ================ OLLAMA (lfm2.5) — Simple reusable chat wrapper ================== #
def ollama_chat(prompt: str, timeout: int = 90) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except requests.exceptions.Timeout:
        print("[Code Assistant]: lfm2.5 timed out.")
        return ""
    except Exception as e:
        print(f"[Code Assistant - Ollama Error]: {e}")
        return ""

#  FILE CHUNKING — split by function/class boundaries (Python only)
def chunk_python_file(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        print("[Code Assistant]: Could not parse as Python — falling back to line chunking.")
        return chunk_by_lines(source)

    lines = source.splitlines(keepends=True)
    chunks = []
    last_end = 0

    top_level_nodes = [
        node for node in ast.iter_child_nodes(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]

    if not top_level_nodes:
        # No functions/classes at all (e.g. a pure script) — chunk by lines instead
        return chunk_by_lines(source)

    for node in top_level_nodes:
        start = node.lineno - 1  # ast line numbers are 1-indexed
        end = node.end_lineno  # already 1-indexed inclusive; slicing handles it naturally
        chunk_text = "".join(lines[last_end:end])
        if chunk_text.strip():
            chunks.append(chunk_text)
        last_end = end

    # Catch any trailing code after the last function/class
    if last_end < len(lines):
        trailing = "".join(lines[last_end:])
        if trailing.strip():
            chunks.append(trailing)
    return chunks

# ================ Chunking for Non-Python files =================#
def chunk_by_lines(source: str) -> list[str]:
    lines = source.splitlines(keepends=True)
    return [
        "".join(lines[i:i + FALLBACK_CHUNK_LINES])
        for i in range(0, len(lines), FALLBACK_CHUNK_LINES)
    ]


def chunk_file(filepath: str, source: str) -> list[str]:
    """Picks the right chunking strategy based on file extension."""
    if filepath.endswith(".py"):
        return chunk_python_file(source)
    return chunk_by_lines(source)

#================= LFM2.5 — CODE REVIEW ====================#
def review_code(filepath: str) -> str:
    if not os.path.exists(filepath):
        return f"I couldn't find a file at '{filepath}', Master."

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    if not source.strip():
        return f"'{os.path.basename(filepath)}' is empty, Master. Nothing to review."

    chunks = chunk_file(filepath, source)
    print(f"[Code Assistant]: Reviewing '{filepath}' in {len(chunks)} chunk(s)...")

    findings = []
    for i, chunk in enumerate(chunks):
        prompt = (
            "You are a code reviewer. Review the following code chunk for bugs, "
            "bad practices, unclear naming, or missing error handling. "
            "Be concise — bullet points only, no fluff, no restating the code. "
            "If the chunk looks fine, just say 'No issues found.'\n\n"
            f"Code:\n```\n{chunk}\n```"
        )
        result = ollama_chat(prompt)
        if result and "no issues found" not in result.lower():
            findings.append(f"[Section {i+1}]\n{result}")

    if not findings:
        return f"I reviewed '{os.path.basename(filepath)}', Master — looks clean, no issues found."

    summary = "\n\n".join(findings)
    print(f"[Code Review]:\n{summary}")
    return f"I reviewed '{os.path.basename(filepath)}', Master. Found {len(findings)} section(s) with notes. Check the terminal for details."

# ============== LFM2.5 — AUTO-COMMENTING (with diff preview + confirmation) ====================#
def generate_commented_version(filepath: str) -> str:
    if not os.path.exists(filepath):
        return f"I couldn't find a file at '{filepath}', Master.", None

    with open(filepath, "r", encoding="utf-8") as f:
        original_source = f.read()

    if not original_source.strip():
        return f"'{os.path.basename(filepath)}' is empty, Master. Nothing to comment.", None

    chunks = chunk_file(filepath, original_source)
    print(f"[Code Assistant]: Generating comments for '{filepath}' in {len(chunks)} chunk(s)...")

    commented_chunks = []
    for i, chunk in enumerate(chunks):
        prompt = (
            "You are a code documentation assistant. Add ONE short inline comment "
            "per line of code below, explaining what that line does. "
            "Preserve the EXACT original code — do not change logic, indentation, "
            "or formatting. Only add comments. Return ONLY the commented code, "
            "no explanations, no markdown code fences.\n\n"
            f"Code:\n{chunk}"
        )
        result = ollama_chat(prompt)
        if not result:
            print(f"[Code Assistant]: Chunk {i+1} failed to generate comments — keeping original for this chunk.")
            commented_chunks.append(chunk)
        else:
            commented_chunks.append(result)

    commented_source = "\n".join(commented_chunks)

    # Save to a temp file — original is NOT touched yet
    temp_path = filepath + ".commented_preview.py" if filepath.endswith(".py") else filepath + ".commented_preview"
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(commented_source)

    diff = list(difflib.unified_diff(
        original_source.splitlines(),
        commented_source.splitlines(),
        fromfile="original",
        tofile="commented",
        lineterm="",
    ))

    added_lines = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    print(f"[Code Assistant]: Preview saved to '{temp_path}'.")
    print("\n".join(diff[:60]))  # Print a capped preview to terminal — full diffs can be huge

    summary = (
        f"I've drafted comments for '{os.path.basename(filepath)}', Master — "
        f"about {added_lines} lines changed. Want me to apply it, or discard the preview?"
    )
    return summary, temp_path


def apply_commented_version(filepath: str, temp_path: str) -> str: #Called after the user confirms they want to keep the commented version.
    if not os.path.exists(temp_path):
        return "I couldn't find the preview file anymore, Master. It may have already been cleaned up."

    backup_name = os.path.basename(filepath) + ".backup"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(filepath, backup_path)
    print(f"[Code Assistant]: Backed up original to '{backup_path}'.")

    shutil.move(temp_path, filepath)
    return f"Done, Master. '{os.path.basename(filepath)}' has been updated. The original is backed up in case you change your mind."


def discard_commented_version(temp_path: str) -> str:
    #Called when the user declines the commented preview.
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return "No problem, Master. Discarded the preview — your original file is untouched."

#  LFM2.5 — AUTO-GENERATED COMMIT MESSAGES (with confirmation)
def generate_commit_message(repo_path: str) -> tuple[str, str | None]:
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        return f"'{repo_path}' doesn't look like a git repository, Master.", None, False
    used_unstaged = False

    try:
        diff_result = subprocess.run(
            ["git", "diff", "--staged"],
            cwd=repo_path, capture_output=True, text=True, timeout=15
        )
        diff_output = diff_result.stdout.strip()

        if not diff_output:
            # Nothing staged — check unstaged changes instead, but warn the user
            diff_result = subprocess.run(
                ["git", "diff"],
                cwd=repo_path, capture_output=True, text=True, timeout=15
            )
            diff_output = diff_result.stdout.strip()
            if diff_output:
                used_unstaged = True
                print("[Code Assistant]: No staged changes found — using unstaged diff instead. "
                      "Remember to 'git add' before committing.")

        if not diff_output:
            return "There's nothing to commit, Master. No staged or unstaged changes detected.", None, False

    except subprocess.TimeoutExpired:
        return "Git took too long to respond, Master.", None, False
    except Exception as e:
        print(f"[Code Assistant - Git Error]: {e}")
        return "Something went wrong reading the git diff, Master.", None, False

    # Cap diff size sent to the model — very large diffs get truncated
    max_diff_chars = 6000
    truncated = len(diff_output) > max_diff_chars
    diff_for_prompt = diff_output[:max_diff_chars]

    prompt = (
        "You are a git commit message generator. Given the diff below, write "
        "ONE concise commit message in conventional commit style "
        "(e.g. 'fix: handle empty response from API'). "
        "Return ONLY the commit message, nothing else — no quotes, no explanation.\n\n"
        f"Diff{' (truncated)' if truncated else ''}:\n{diff_for_prompt}"
    )

    draft = ollama_chat(prompt)
    if not draft:
        return "I couldn't generate a commit message right now, Master.", None, False

    draft = draft.strip().strip('"').strip("'")
    note = " These are unstaged changes — I'll stage them all before committing." if used_unstaged else ""
    spoken = f"Here's my draft commit message, Master: \"{draft}\". Should I commit with this message?"
    return spoken, draft, used_unstaged


def confirm_commit(repo_path: str, message: str, stage_first: bool = False) -> str: #Actually runs `git commit -m <message>` — ONLY called after the user has explicitly confirmed the drafted message.
    try:
        if stage_first:
            #Stage the changes first by adding git add -A
            add_result = subprocess.run(
                ["git", "add", "-A"],
                cwd=repo_path, capture_output=True, text=True, timeout=15
            )
            if add_result.returncode != 0:
                print(f"[Code Assistant - Git Add Error]: {add_result.stderr}")
                return f"I couldn't stage the changes, Master. Git said: {add_result.stderr.strip()[:150]}"
        #Proceed to commit once staged vio git commit -m
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path, capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
                print(f"[Code Assistant - Git Commit Error]: {result.stderr}")
                return f"The commit failed, Master. Git said: {result.stderr.strip()[:150]}"
        print(f"[Code Assistant]: Commit successful.\n{result.stdout}")
        return "Committed, Master."
    except Exception as e:
        print(f"[Code Assistant - Git Error]: {e}")
        return "Something went wrong while committing, Master."

#  GROQ — SMART ERROR SPOTTING & DEBUGGING
def diagnose_error(filepath: str, error_message: str) -> str:
    if not os.path.exists(filepath):
        return f"I couldn't find '{filepath}' to diagnose against, Master."

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    # Cap source size sent to Groq — keep it focused and fast
    max_chars = 8000
    source_for_prompt = source[:max_chars]

    prompt = (
        "You are a debugging assistant. Given the error message and the relevant code below, "
        "diagnose the likely root cause and recommend a specific fix. "
        "Be concise and direct. Use this format:\n"
        "ROOT CAUSE: <one or two sentences>\n"
        "FIX: <specific, actionable suggestion>\n\n"
        f"Error message:\n{error_message}\n\n"
        f"Relevant code from '{os.path.basename(filepath)}':\n```\n{source_for_prompt}\n```"
    )

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,   # Lower temperature — we want a focused, confident diagnosis, not creative variation
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Code Assistant - Groq Error]: {e}")
        return "I couldn't reach Groq to diagnose that error, Master."


#  GROQ — REFACTOR SUGGESTIONS

# A function/file longer than this many lines is flagged as a refactor candidate
REFACTOR_LINE_THRESHOLD = 50

def suggest_refactor(filepath: str) -> str: #Checks if the file (or individual functions within it) are too long, and if so, asks Groq for a refactor recommendation.
    if not os.path.exists(filepath):
        return f"I couldn't find '{filepath}', Master."

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    total_lines = len(source.splitlines())
    long_functions = []

    if filepath.endswith(".py"):
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    length = node.end_lineno - node.lineno
                    if length > REFACTOR_LINE_THRESHOLD:
                        long_functions.append((node.name, length))
        except SyntaxError:
            pass  # Fall through to whole-file length check only

    if not long_functions and total_lines <= REFACTOR_LINE_THRESHOLD * 3:
        return f"'{os.path.basename(filepath)}' looks reasonably sized, Master. No refactor needed right now."

    # Build a focused prompt — mention which functions triggered the flag
    flagged_desc = (
        ", ".join(f"'{name}' ({length} lines)" for name, length in long_functions)
        if long_functions else f"the file as a whole ({total_lines} lines)"
    )

    max_chars = 8000
    prompt = (
        "You are a senior software engineer giving refactor advice. "
        f"The following code has flagged sections that may be too long: {flagged_desc}. "
        "Suggest a concrete refactor approach — what to extract, split, or restructure. "
        "Be specific and concise. Do NOT rewrite the whole file — just describe the approach.\n\n"
        f"Code:\n```\n{source[:max_chars]}\n```"
    )

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=350,
            temperature=0.4,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Code Assistant - Groq Error]: {e}")
        return "I couldn't reach Groq for refactor suggestions, Master."