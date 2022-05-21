from multiprocessing.sharedctypes import Value
from operator import itemgetter
import re
import numpy


player = ["total_id1", "total_id2", "total_id3", "total_id4", "total_id5", "total_id6"]
score = numpy.array([3, 13, 9, 7, 42, 3])

win = min(score)

print(win)

winner = numpy.array(player)[score == win]

print(winner)