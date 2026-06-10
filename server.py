"""
server.py — Flask backend for Static Code Analyzer Web UI.
Run: python3 server.py
Open: http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
import os, tempfile

app = Flask(__name__, static_folder="frontend")


@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data     = request.get_json()
    code     = data.get("code", "")
    language = data.get("language", "c").lower()
    if not code.strip():
        return jsonify({"error": "No code provided"}), 400
    ext = ".c" if language == "c" else ".py"
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name
        if language == "c":
            from core.c_runner import analyze_c
            violations = analyze_c(tmp_path)
        else:
            from core.runner import analyze_python
            violations = analyze_python(tmp_path)
        os.unlink(tmp_path)
        return jsonify({
            "violations": [
                {"rule": v.rule, "message": v.message, "line": v.line,
                 "severity": v.severity.value, "phase": v.phase.value}
                for v in violations
            ],
            "total":    len(violations),
            "errors":   sum(1 for v in violations if v.severity.value == "ERROR"),
            "warnings": sum(1 for v in violations if v.severity.value == "WARNING"),
            "infos":    sum(1 for v in violations if v.severity.value == "INFO"),
            "lines":    len(code.splitlines()),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  Static Code Analyzer — Web UI")
    print("  Open: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)
