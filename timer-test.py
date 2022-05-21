#from time import sleep

#print("前半スタート！")

#sleep(3)

#print("前半終了です！")




#print("後半スタート！")

#sleep(3)

#print("ゲーム終了です！")



import numpy

label_prediction = numpy.array([0,0,1,1,0,1])
data = ["a","b","C","D","e","F"]

print (numpy.array(data)[label_prediction==1])





win = [i for i,v in enumerate(score) if v == max(score)]

#l = [1, 3, 5, 2, 5]

#li = [i for i, v in enumerate(l) if v == max(l)]
#print(li)

winner = itemgetter(win)(player)

print(winner)
