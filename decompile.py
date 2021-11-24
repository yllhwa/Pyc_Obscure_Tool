import dis
import marshal
f=open('test.pyc', 'rb').read()
co=marshal.loads(f[16:])
dis.dis(co)