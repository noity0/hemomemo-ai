import sys; sys.path.insert(0, r'D:\DigitalBrain')
from model.understand import default_token_chat
b = default_token_chat()
for q in ['frontend basics', 'sql vs nosql', 'python hello world', 'code hello world in java', 'code i love you in java', 'code salam in html', 'what is rest crud', 'code hello world in python']:
    t, m = b.respond(q)
    print('%-28s -> %-11s tok=%s' % (q, m.get('source'), m.get('tokens')))
    print('    ans=%s' % (t or '')[:110].replace(chr(10), ' '))
