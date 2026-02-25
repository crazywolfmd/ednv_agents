import bcrypt

stored = "$2a$12$XLYcLfYecBmiLSi/.MnMF.4U1FzDOmsWvbVFX3HN8ixaaTeD9h/Tm"
candidate = "test"

print(bcrypt.checkpw(candidate.encode("utf-8"), stored.encode("utf-8")))
