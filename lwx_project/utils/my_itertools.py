from collections import OrderedDict


def dedup_list(l: list):
    return list(OrderedDict.fromkeys(l))

if __name__ == '__main__':
    a = [1,2,2,2,2,2,3,4,5,6,6,6,6,7,8,8]
    print(dedup_list(a))