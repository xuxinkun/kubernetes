import json


def _generate_policy(user):
    policy = {
        "apiVersion": "abac.authorization.kubernetes.io/v1beta1",
        "kind": "Policy",
        "spec": {
            "user": user,
            "namespace": user,
            "resource": "pod",
            "nonResourcePath": "*",
            "apiGroup": "*"
        }
    }
    return json.dumps(policy)


def _generate_user(user, passwd):
    return '%s,%s,%s' % (passwd, user, user)


def get_pass(l):
    w = l.split(',')
    return w[0].strip(), w[1].strip()


def write_file():
    policies = []
    users = []

    f = open('passwd', 'r')
    l = f.readline()
    while l:
        user, passwd = get_pass(l)
        users.append(_generate_user(user, passwd))
        policies.append(_generate_policy(user))
        l = f.readline()
    f.close()

    f = open('policy.json', 'w')
    f.write('\n'.join(policies))
    f.close()
    f = open('user.csv', 'w')
    f.write('\n'.join(users))
    f.close()


if __name__ == '__main__':
    write_file()
