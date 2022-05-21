from functools import total_ordering
from itertools import count

#st = "やっぱりトマトと人参だなそっちの意見は？"

#st = st + "トマトは分かる。大根おろしとかはどうだろうか"


#count_one = st.count("トマト")
#count_two = st.count("は")

#total = count_one + count_two

#print(st)
#print(total)

#一人一人、idごとに1つの文字列を作成　→　終了と同時に一斉に数え上げる



text = input()
score = text.count("トマト")
print(score)
