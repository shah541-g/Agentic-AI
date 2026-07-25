import re

lines = [
    'From stephen.marquard@uct.ac.za Sat Jan 5 09:14:16 2008',
    'X-DSPAM-Confidence: 0.8475',
    'X-DSPAM-Confidence: 0.7654',
    'X-DSPAM-Confidence: 0.9987',
    'Received: from mail.example.com',
    'Subject: Meeting tomorrow',
    'X-DSPAM-Confidence: 0.123',
    'To: user@example.com',
    'X-DSPAM-Confidence: 0.5000',
    'Message-ID: <abc123@example.com>',
    'X-DSPAM-Probability: 0.95',   # similar but should NOT match
    'X-DSPAM-Confidence: abc',     # invalid confidence value
    'Date: Sat, 5 Jan 2008 09:14:16 +0000',
    'X-DSPAM-Confidence: 0.9999',
    'Hello, how are you?',
]

confidenceScores = []
# for line in lines:
#   if re.search(r"^X-DSPAM-Confidence: ([0-9]+\.[0-9]+)*", line):
#     confidenceScores.extend(re.findall(r"([0-9]+\.[0-9]+)",line))
    
for line in lines:
  match = re.search(r'^X-DSPAM-Confidence: ([0-9.]+)', line)
  if match:
    confidenceScores.append(float(match.group(1)))
print(confidenceScores)