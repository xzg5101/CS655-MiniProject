import hashlib
import math

alList = [ "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", 
    "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "a", "b", "c", "d", "e", 
    "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]

# for a number, find the corresponding password
def numToStr(num)->str:
    if num < 0 or num > 380204031:
        return ""

    limit = ""
    while num > 0:
        limit = alList[(num%52)] + limit
        num = num//52

    while(len(limit) < 5):
        limit = "A"+limit

    return limit

def strToNum(s)->int:
    num = 0
    for i in range(len(s)):
        num += alList.index(s[i]) * math.pow(52, len(s)-1-i)
    return int(num)


def crack2(num1, num2, result)->str:
    print("num1", num1, "num2", num2)
    i = num1
    while i < num2:        
        aStr = numToStr(i)
        locMd5 = hashlib.md5(aStr.encode()).hexdigest()
        print("checking", i,":",aStr, ": ", locMd5)
        if locMd5 == result:
            print("answer found to be", aStr)
            return aStr
        i += 1
        
    print("Answer not found")
    return ""



str = "AABAA"
result = hashlib.md5(str.encode()).hexdigest()

lrange = 380204031//100
print("range is ", lrange)
#crack2(0, range, result)
tostr = numToStr(lrange)

print(tostr)
















#alStr = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


'''
def crack(str1, str2, result):

    startList = []

    for i in str1:
        startList.append(alList.index(i))

    for i in range( len(alList)):
        tempS = "" + alList[i]
        for j in range( len(alList)):
            tempS += alList[j]
            for k in range( len(alList)):
                tempS += alList[k]
                for l in range( len(alList)):
                    tempS += alList[l]
                    for m in range(len(alList)):
                        tempS += alList[m]
                        locMd5 = hashlib.md5(tempS.encode()).hexdigest()
                        print("checking", tempS, ": ", locMd5)
                        if locMd5 == result:
                            print("answer found to be", tempS)
                            return tempS
                        
                        if tempS == str2:
                            print("Answer not found")
                            return ""'''





