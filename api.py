from argon2 import PasswordHasher

ph = PasswordHasher()

print(ph.hash('tnwlsl98@'))
print('$argon2id$v=19$m=65536,t=3,p=4$sPIc8jhcTU5/gvx2ZeymBA$oaYq8KyFEb+xI25EJmUsTRWI9Rn+RTlm1X5cSELQxIs')