def invlog_scale(x):
    m=10
    return (pow(2,x * m)-1)/(pow(2,m)-1)

if __name__=="__main__":
    y = invlog_scale(0.0)
    print("y=", y)
    y = invlog_scale(.98)
    print("y=", y)
    y = invlog_scale(1.0)
    print("y=", y)
