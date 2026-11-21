# Chapter 11: Regular Expressions (Regex) — Notes

## 1. What Is a Regular Expression?

- So far we have read files and extracted data using string methods like `split()`, `find()`, and slicing. This task is so common that Python provides a powerful module for it: **`re`**.
- A regex is almost its own small programming language for **searching** and **parsing** strings.
- You must import the module before using it: `import re`
- A good place to practice: [regex101.com](https://regex101.com/)

### `re.search()` — Basic Use

```python
import re
hand = open('mbox-short.txt')
for line in hand:
    line = line.rstrip()
    if re.search('From:', line):
        print(line)
```

- This prints only the lines that contain `From:`.
- This example doesn't show the real power of regex (`line.find()` would do the same). The power comes from **special characters**.

### `^` — Beginning of a Line

```python
if re.search('^From:', line):
    print(line)
```

- `^From:` matches only lines that **start** with `From:` (like `startswith()`).

---

## 2. Character Matching

### `.` (Period) — Wildcard

- Matches **any single** character.
- `F..m:` matches `From:`, `Fxxm:`, `F12m:`, `F!@m:`

```python
if re.search('^F..m:', line):
    print(line)
```

### `*` and `+` — Repetition

| Symbol | Meaning |
|--------|---------|
| `*` | zero **or more** times |
| `+` | **one or more** times |

```python
if re.search('^From:.+@', line):
    print(line)
```

- `^From:.+@` matches lines that start with `From:`, followed by one or more characters, followed by an `@`.
- Example match: `From: stephen.marquard@uct.ac.za`

### Greedy vs. Non-Greedy

- `+` and `*` are **greedy**: they try to match as much text as possible.
- Given `From: stephen.marquard@uct.ac.za, csev@umich.edu, and cwen@iupui.edu`:
  - `.+@` expands to the **last** `@` (the one in `cwen@iupui.edu`).
- **Non-greedy**: add a `?` to get `.+?` or `.*?`, which matches up to the **first** `@`.

---

## 3. Extracting Data with `findall()`

- `findall()` returns a **list** of all substrings that match the regex.

```python
import re
s = 'A message from csev@umich.edu to cwen@iupui.edu about meeting @2PM'
lst = re.findall(r'\S+@\S+', s)
print(lst)
# ['csev@umich.edu', 'cwen@iupui.edu']
```

- `\S` matches a **non-whitespace** character, so `\S+` matches as many non-whitespace characters as possible.
- The `r` prefix makes it a **raw string**, so Python doesn't treat backslashes as escape characters (like `\n`). Always use it for regex.
- `@2PM` is not matched because there is no non-blank character before the `@`.

### Extracting Emails from a File

```python
for line in hand:
    line = line.rstrip()
    x = re.findall(r'\S+@\S+', line)
    if len(x) > 0:
        print(x)
```

- Problem: the output includes unwanted characters, such as `<source@collab.sakaiproject.org>;` and `apache@localhost)`.

### Square Brackets `[ ]` — Character Sets

- `[a-zA-Z0-9]` matches **any one** of those characters.
- Improved regex:

```
[a-zA-Z0-9]\S*@\S*[a-zA-Z]
```

- Meaning: starts with a letter or digit, then zero or more non-blank characters, then `@`, then zero or more non-blank characters, ending with a letter.
- We use `*` instead of `+` because the first `[a-zA-Z0-9]` already accounts for one character.
- Side effect: trailing characters like `>;` are cut off, because the match must **end with a letter**.
- `*` and `+` apply only to the **single character immediately to their left**.

---

## 4. Combining Searching and Extracting

Target lines:

```
X-DSPAM-Confidence: 0.8475
X-DSPAM-Probability: 0.0000
```

Regex to select the lines:

```
^X-.*: [0-9.]+
```

- Starts with `X-`, then anything (`.*`), then `: ` (colon and space), then one or more digits or periods (`[0-9.]+`).
- **Important:** inside square brackets, `.` is a literal period, not a wildcard.

### Parentheses `( )` — Extract Only Part of the Match

- Parentheses are ignored for matching purposes.
- With `findall()`, they tell Python to return **only that portion** of the match.

```python
x = re.findall(r'^X-.*: ([0-9.]+)', line)
if len(x) > 0:
    print(x)
# ['0.8475'] ['0.0000'] ...
```

- The results are still a **list of strings**, so you need to convert them with `float()`.

### Extracting Revision Numbers

Line: `Details: http://source.sakaiproject.org/viewsvn/?view=rev&rev=39772`

```python
x = re.findall(r'^Details:.*rev=([0-9]+)$', line)
```

- `$` marks the end of the line.
- `[0-9]+` is greedy, so you get the full number (`39772`).

### Extracting the Hour of the Day

Line: `From stephen.marquard@uct.ac.za Sat Jan  5 09:14:16 2008`

```python
x = re.findall('^From .* ([0-9][0-9]):', line)
if len(x) > 0: print(x)
# ['09'] ['18'] ['16'] ...
```

- The older approach used two `split()` calls, which is **brittle code**: it breaks if the format changes even slightly. Regex is shorter and more robust.

---

## 5. The Escape Character `\`

- To match a special character (`^`, `$`, `.`) **literally**, put a backslash before it.

```python
x = 'We just received $10.00 for cookies.'
y = re.findall('\$[0-9.]+', x)
# ['$10.00']
```

- `\$` matches an actual dollar sign, not the end of a line.

---

## 6. Summary — Special Characters Cheat Sheet

| Pattern | Meaning |
|---------|---------|
| `^` | beginning of the line |
| `$` | end of the line |
| `.` | any single character (wildcard) |
| `\s` | a whitespace character |
| `\S` | a non-whitespace character |
| `*` | zero or more times |
| `*?` | zero or more times, **non-greedy** |
| `+` | one or more times |
| `+?` | one or more times, **non-greedy** |
| `?` | zero or one time |
| `??` | zero or one time, non-greedy |
| `[aeiou]` | any one character in the set |
| `[a-z0-9]` | range: a lowercase letter or a digit |
| `[^A-Za-z]` | **inverted** set: anything except letters |
| `( )` | extract only this portion with `findall()` |
| `\b` | empty match at the start or end of a word |
| `\B` | empty match **not** at the start or end of a word |
| `\d` | any digit, same as `[0-9]` |
| `\D` | any non-digit, same as `[^0-9]` |

---

## 7. Bonus: Unix/Linux `grep`

- `grep` stands for **G**eneralized **R**egular **E**xpression **P**arser. It does much the same job as Python's `search()`.

```bash
$ grep '^From:' mbox-short.txt
```

- Difference: `grep` doesn't support `\S`. Use `[^ ]` instead (any character except a space).

---

## 8. Debugging Tips

```python
>>> help()
>>> import re
>>> dir(re)          # list all methods in the module
>>> help(re.search)  # documentation for a specific method
```

- Useful `re` methods: `compile`, `findall`, `finditer`, `match`, `search`, `split`, `sub`, `subn`, `escape`.

---

## 9. Glossary

- **Brittle code**: code that works only for a particular input format and breaks when the format deviates.
- **Greedy matching**: `+` and `*` expanding outward to match the largest possible string.
- **grep**: a Unix command that searches files for lines matching a regular expression.
- **Regular expression**: a language for expressing complex search strings.
- **Wild card**: a character that matches any character (`.` in regex).

---

## 10. Exercises

**Exercise 1 — `grep.py`**
Ask the user for a regular expression and count how many lines in `mbox.txt` match it.

```
Enter a regular expression: ^Author
mbox.txt had 1798 lines that matched ^Author
Enter a regular expression: ^X-
mbox.txt had 14368 lines that matched ^X-
Enter a regular expression: java$
mbox.txt had 4175 lines that matched java$
```

**Exercise 2 — Average Revision Number**
Extract the number from lines like `New Revision: 39772` using `findall()`, compute the average, and print it as an **integer**.

```
Enter file:mbox.txt        -> 38549
Enter file:mbox-short.txt  -> 39756
```

---

## Quick Recap

1. `re.search()` checks whether a match exists.
2. `re.findall()` returns a list of all matches.
3. Use `( )` to extract only the part you need.
4. Always use raw strings: `r'...'`.
5. Remember the difference between greedy (`+`, `*`) and non-greedy (`+?`, `*?`).
6. Use `\` to match special characters literally.

*Source: Python for Everybody, Chapter 11 — Charles R. Severance, CC BY 4.0*
