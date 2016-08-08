import etcd
import os
import json
import uuid
import pprint

def get_container_info(l):
    p = l.split(",")
    container_name = p[0].strip()
    host_name = p[1].strip()
    if len(p) == 2:
        name_space = 'default'
    elif len(p) == 3:
        name_space = p[2].strip()
    else:
        raise Exception('Erro when get container info from %s' % l)
    return container_name, host_name, name_space


def init_etcd_client():
    etcd_host = os.getenv('ETCD_HOST', '10.8.65.91')
    etcd_port = int(os.getenv('ETCD_PORT', '4001'))
    client = etcd.Client(host=etcd_host, port=etcd_port)
    return client


def _generate_pod_info(container_name, host_ip, name_space):
    info = {
        "kind": "Pod",
        "apiVersion": "v1",
        "metadata": {
            "name": container_name,
            "namespace": name_space,
            "selfLink": "/api/v1/namespaces/%s/pods/%s" % (name_space, container_name),
            "uid": container_name,
            "creationTimestamp": "2016-07-24T02:36:03Z",
            "labels": {
                "name": "busybox",
                "role": "master"
            }
        },
        "spec": {
            "containers": [{
                "name": container_name,
                "image": "busybox",
                "command": ["sleep", "360000"],
                "resources": {
                },
                "terminationMessagePath": "/dev/termination-log",
                "imagePullPolicy": "Never"
            }],
            "restartPolicy": "Never",
            "terminationGracePeriodSeconds": 30,
            "dnsPolicy": "ClusterFirst",
            "host": host_ip,
            "nodeName": host_ip,
            "securityContext": {
            }
        },
        "status": {
            "phase": "Running",
            "conditions": [{
                "type": "Ready",
                "status": "True",
                "lastProbeTime": None,
                "lastTransitionTime": "2016-07-24T02:25:56Z"
            }],
            "hostIP": host_ip,
            "podIP": "4.0.0.8",
            "startTime": "2016-07-24T02:25:47Z",
            "containerStatuses": [{
                "name": container_name,
                "state": {
                    "running": {
                        "startedAt": "2016-07-24T02:25:55Z"
                    }
                },
                "lastState": {

                },
                "ready": True,
                "restartCount": 0,
                "image": "busybox",
                "imageID": "docker://sha256:2b8fd9751c4c0f5dd266fcae00707e67a2545ef34f9a29354585f93dac906749",
                "containerID": "docker://f357245c0fd5e173a935dba127130615d1d2c55801d12a6ca070d9fadb0b6f06"
            }]
        }
    }
    return json.dumps(info)

def _generate_namespace_info(name_space):
    uid = uuid.uuid4()
    info = {
        "kind": "Namespace",
        "apiVersion": "v1",
        "metadata": {
            "name": name_space,
            "uid": '%s' % uid,
            "creationTimestamp": "2016-07-20T07:17:16Z"
        },
        "spec": {
            "finalizers": ["kubernetes"]
        },
        "status": {
            "phase": "Active"
        }
    }
    return json.dumps(info)

def _ensure_namespace(name_spaces):

    for name_space in name_spaces:
        client = init_etcd_client()
        ns_path = '/registry/namespaces/%s' %name_space
        try:
            client.read(ns_path)
        except etcd.EtcdKeyNotFound:
            info = _generate_namespace_info(name_space)
            client.write(ns_path, info)

        pod_dir_path = '/registry/pods/%s' % name_space
        try:
            client.read(pod_dir_path)
        except etcd.EtcdKeyNotFound:
            client.write(pod_dir_path, None, dir=True)

def save_container_to_etcd(hosts):
    client = init_etcd_client()
    containers = []
    name_spaces = set()

    container_file = open('container.csv', 'r')
    l = container_file.readline()
    while l:
        c = get_container_info(l)
        containers.append(c)
        name_spaces.add(c[2])
        l = container_file.readline()
    container_file.close()
    _ensure_namespace(name_spaces)

    for c in containers:
        container_name, host_name, name_space = c
        host_ip = hosts.get(host_name)
        if host_ip is not None:
            info = _generate_pod_info(container_name, host_ip, name_space)
            path = '/registry/pods/%s/%s' % (name_space, container_name)
            try:
                pre_info = client.read(path)
                if pre_info == info:
                    continue
            except etcd.EtcdKeyNotFound:
                print '%s is not found. Write it.' % path
            finally:
                print 'Write %s into etcd.' % path
                client.write(path, info)
        else:
            print 'host_name %s cannot be resolved to ip.' % host_name

def _generate_host_info(host_name, host_ip):
    uid = uuid.uuid4()
    info = {
        "kind": "Node",
        "apiVersion": "v1",
        "metadata": {
            "name": host_name,
            "selfLink": "/api/v1/nodes/%s" % host_name,
            "uid": "%s" % uid,
            "creationTimestamp": "2016-07-20T07:18:54Z",
            "labels": {
                "kubernetes.io/hostname": host_name
            }
        },
        "spec": {
            "externalID": host_ip
        },
        "status": {
            "capacity": {
                "cpu": "1",
                "memory": "1016860Ki",
                "pods": "110"
            },
            "allocatable": {
                "cpu": "1",
                "memory": "1016860Ki",
                "pods": "110"
            },
            "conditions": [{
                "type": "OutOfDisk",
                "status": "Unknown",
                "lastHeartbeatTime": "2016-07-20T07:20:02Z",
                "lastTransitionTime": "2016-07-20T07:30:59Z",
                "reason": "NodeStatusUnknown",
                "message": "Kubelet stopped posting node status."
            },
            {
                "type": "Ready",
                "status": "Unknown",
                "lastHeartbeatTime": "2016-07-20T07:20:02Z",
                "lastTransitionTime": "2016-07-20T07:30:59Z",
                "reason": "NodeStatusUnknown",
                "message": "Kubelet stopped posting node status."
            }],
            "addresses": [{
                "type": "LegacyHostIP",
                "address": host_ip
            },
            {
                "type": "InternalIP",
                "address": host_ip
            }],
            "daemonEndpoints": {
                "kubeletEndpoint": {
                    "Port": 10250
                }
            },
            "nodeInfo": {
                "machineID": "bfef1e6bfd0747eca310bb21fcc0ecb5",
                "systemUUID": "1D632E5B-B046-468F-B27C-AE88DDCD1172",
                "bootID": "2900f117-63ee-44a9-8014-42aa6a86cd9e",
                "kernelVersion": "3.10.0-327.el7.x86_64",
                "osImage": "CentOS Linux 7 (Core)",
                "containerRuntimeVersion": "docker://1.10.3",
                "kubeletVersion": "v1.2.0",
                "kubeProxyVersion": "v1.2.0"
            },
            "images": None
        }
    }
    return json.dumps(info)

def save_host_to_etcd():
    client = init_etcd_client()
    hosts = {}

    host_file = open('host.csv', 'r')
    l = host_file.readline()
    while l:
        host_name, host_ip, name_space =get_container_info(l)
        hosts[host_name] = host_ip
        l = host_file.readline()
    host_file.close()

    for host_name, host_ip in hosts.iteritems():
        info = _generate_host_info(host_name, host_ip)
        path = '/registry/minions/%s' % (host_ip)
        try:
            pre_info = client.read(path)
            if pre_info == info:
                continue
        except etcd.EtcdKeyNotFound:
            print '%s is not found. Write it.' % path
        finally:
            client.write(path, info)
    return hosts

def main():
    hosts = save_host_to_etcd()
    print 'Read Hosts:'
    print '*' * 10
    pprint.pprint(hosts)
    save_container_to_etcd(hosts)

if __name__ == '__main__':
    main()