# crontab-lint

A static analyzer and validator for crontab expressions that checks for overlapping schedules and common mistakes.

## Installation

```bash
pip install crontab-lint
```

## Usage

Validate a crontab file directly from the command line:

```bash
crontab-lint /etc/cron.d/myjobs
```

Or use it programmatically in your Python code:

```python
from crontab_lint import CrontabLinter

linter = CrontabLinter()
results = linter.check("*/5 * * * * /usr/bin/backup.sh")

for issue in results:
    print(f"[{issue.severity}] {issue.message}")
```

### Example Output

```
[WARNING] Line 3: Schedule '*/5 * * * *' overlaps with line 7 ('* */1 * * *')
[ERROR]   Line 9: Invalid day-of-week value '8' (valid range: 0-7)
[INFO]    Line 12: Consider using @daily instead of '0 0 * * *'
```

### Checks Performed

- Invalid field values and out-of-range numbers
- Overlapping or redundant schedule expressions
- Unreachable schedules (e.g., February 31st)
- Non-standard syntax and common typos
- Missing or malformed commands

## License

This project is licensed under the [MIT License](LICENSE).