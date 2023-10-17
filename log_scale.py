import math

# https://www.geeksforgeeks.org/python-intensity-transformation-operations-on-images/

max = 1.0
c = max/(math.log(1.0 + max))


# def log_scale(x):
#     y = c * math.log(1.0 + x, base)
#     return y


def invlog_scale(x):
    m=10
    return (pow(2,x * m)-1)/(pow(2,m)-1)

if __name__=="__main__":
    print("c=", c)
    x = invlog_scale(.98)
    print("x=", x)
