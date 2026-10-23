# Kubernetes blinded leakage read (40 cleaned issues)

**Who:** Tushar M, or Thejas P Rao if Tushar is unavailable. Not an AI
assistant.

**Rules:**
- Read each issue **as cleaned**. Do not look anything up on GitHub.
- Do not open `blind_key.json`.
- Do not look at any labels or model outputs.

**For each code, record in `blind_log_TEMPLATE.csv`** (save it as
`blind_log_<initials>.csv`):
1. **label_recoverable_from_explicit_cue:** yes or no. Can the issue's
   SIG (network / storage / node), kind (bug vs feature, support or
   cleanup) or priority be read off an explicit cue? For example:
   - a leftover `/command`;
   - label text such as `sig/...` or `priority/...`;
   - a template heading;
   - a SIG team mention;
   - a sentence such as "this is a feature request" or "P0".
2. **which_label_and_cue:** if yes, which label and the cue's text.
3. **text_damaged:** yes or no. Was it cut mid-word, left near-empty by
   stripping, or does it contain a template remnant?
4. **damage_type**, and **notes**.

**When finished:** commit the CSV before anyone opens the key.

**What happens next** (protocol §3.3):
- **A cue that the cleaning rules should have caught:** the rules are
  amended, the dataset is rebuilt and the read is repeated on a new
  sample.
- **A natural reporter phrase:** it stays in, and its rate is reported.
- **Two or more damaged texts:** the cleaning is fixed and the dataset
  rebuilt.

---

## B01

```
Fail to pull docker image from private registry server

Hi, I'm facing the issue below when kubelet tried to pull image from a private registry, and need user authentication:

And I followed the document below, in section "Configuring Nodes to Authenticate to a Private Repository"

[link]

But the issue still exist, seems .dockercfg file didn't take effect when kubelet tried to pull the image, anything else I should do to make it work?

BTW, if I manually do the "docker pull <index_server>/nkwanglei/nodejssample" on the same node, then the image can be pulled successfully.

My kubenetes version is v0.18.2, thanks!
```

---

## B02

```
Remove Set() method from storage.Interface

Set method from storage.Interface:
[link]

is used only in few tests. We should get rid of it completely.
```

---

## B03

```
allowPrivilegeEscalation:false insufficient for privilege escalation prevention

The issue relates to how allowPrivilegeEscalation: false doesn't prevent all forms of privilege escalation through dangerous capabilities.

When a container's security context sets allowPrivilegeEscalation: false, the current validation only blocks CAP_SYS_ADMIN capability. However, other dangerous capabilities that can also lead to privilege escalation are still allowed.

Technical Details:
1. Current Validation:
- Blocks: CAP_SYS_ADMIN when allowPrivilegeEscalation: false
- Allows: CAP_NET_ADMIN, CAP_SYS_MODULE, CAP_SYS_PTRACE, etc.

2. Example:

3. Dangerous Capabilities Still Allowed:
- CAP_NET_ADMIN: Network stack manipulation, potential for network namespace escape
- CAP_SYS_MODULE: Loading kernel modules
- CAP_SYS_PTRACE: Process debugging and memory access
- CAP_DAC_READ_SEARCH: Bypass file permission checks
- CAP_SYS_RAWIO: Direct I/O access
- CAP_AUDIT_CONTROL: Audit system manipulation

Impact:
- False sense of security when using allowPrivilegeEscalation: false
- Privilege escalation still possible through allowed capabilities

Proposed Fix:
Extend the validation to block all dangerous capabilities when allowPrivilegeEscalation is set to false.

I’d love to hear your thoughts! Have you run into situations where `allowPrivilegeEscalation: false` didn’t cut it?
Thanks
```

---

## B04

```
DRA: AllocationMode All errors for incomplete or invalid pools are not per-node failures

An `AllocationMode: All` request returns a plain error when a pool gathered for the candidate node is incomplete or invalid. In `validateDeviceRequest`, same code in the stable, incubating and experimental variants:

Neither wraps `internal.ErrFailedAllocationOnNode`. `DynamicResources.Filter` maps only that sentinel to an `Unschedulable` result for the node; anything else becomes a framework `Error`, and `checkNode` in `findNodesThatPassFilters` cancels the remaining node checks when one shows up.

The other failing cases in the same suite do wrap it. Probe on master `a818af18fe2`, logging `errors.Is(err, ErrFailedAllocationOnNode)` for every case that errors:

Same in all three variants.

`IsIncomplete` does not need a malformed object. `GatherPools` sets it when the generation resolved for the node holds fewer slices than its declared `resourceSliceCount`, which is what a pool looks like while a driver is publishing a new generation.

The check itself looks right and I would leave it alone: a slice that has not arrived may hold another device matching the request, so the allocator cannot know the full set yet.

The classification is the part that looks wrong. Wrapping the sentinel keeps the visible message, since it has no text of its own, and keeps the failure on one node:

Other nodes then keep being evaluated, and if all of them fail the Pod is `Unschedulable`. `EventsToRegister` already lists `ResourceSlice` `Add` and `Update`, so the slice update that finishes the rollout requeues it. The invalid branch wants the same treatment.

`all-devices-of-the-incomplete-pool` in `allocatortesting/allocator_testing.go` already reaches the incomplete branch. Adding this next to the existing `expectError` assertion produces the output above:

No case covers the invalid branch today.

Same classification shape as #141214 and #141338, different trigger.
```

---

## B05

```
[PodLevelResources] In-place pod resize events do not capture pod-level resources

When issuing in-place pod resize requests, you can view the progress of resizes via events:

but the [podResourceSummary object]([link] that gets marshaled for these events doesn't include pod-level resources, meaning that the allocation emitted is incomplete as it does not contain pod-level resources.

There is a TODO for this: [link]
```

---

## B06

```
[Feature] Integrate closely with flannel and/or Calico, via network plugins.

Integrate closely with flannel and/or Calico, via network plugins.
```

---

## B07

```
What are the blockers for running 1000 pods per node.

Hi,

I just started playing with kubernetes on bare-metal servers. I wonder how many pods I can start per server. According to [link] k8s should support 30 pods/node, but for bare metal deployments it is very low. Do you have some list of blockers to scale it up to 1000 pods/node ( or at least few 100s ) ?
I am mostly interested in kubelet/docker limitations.
```

---

## B08

```
align by socket not work when pod using multiple gpu card

I am running an AI application and expect to achieve the highest performance by using the Topology Manager to establish NUMA affinity binding between CPU and GPU.

so i restart kubelet with such options

then I use multiple GPU cards,
if the number of GPU cards are more than one socket, the allocated cpu and gpu are not aligned by socket.

The CPU cores requested by the pod should be from the NUMA node where the GPUs are located.

create pod with more than one nvidia gpu cards, like two gpu cards

1. create pod with 5 nvidia gpu cards
there is one gpu card on every numa and one socket consists of 4 numa node, so i request 5 cards thus gpus have to cross socket.

3. waiting pod running

4. check gpu and cpu core numa topology

5. we can see the allocated gpus are on numa node1,4,5,6,7 while cpus are on numa node1,2,3,4,5, they are not aligned.
```

---

## B09

```
Create a cleaner interface between `cmd/kube-proxy` and `pkg/proxy/{iptables,ipvs,nftables,winkernel}`

Right now there is no clear interface between `cmd/kube-proxy` and `pkg/proxy/{iptables,ipvs,nftables,winkernel}`. For example, if kube-proxy wants to create an IPVS proxier, it does:

[link]

Besides just being really messy, this level of intertwinedness makes it difficult to think about how we might move a backend out of tree (as in [link]
```

---

## B10

```
kubelet /stats/summary includes terminated init container in memory.usageBytes

For a pod with an init container that copies some files, the `memory.usageBytes` value reported by `kubelet`'s `/stats/summary` endpoint includes the memory consumption of the init container forever, even though the init container has terminated already.

The value of `memory.usageBytes` differs significantly from what `kubectl top pod` reports for the same pod.

Here is a screenshot where the kubelet reports around 100 MB while `kubectl top` and `k9s` both report 0 MB. (My assumption is that 0 MB is correct for this container and 100 MB is wrong.)

(For the record, kubelet also reports 0 MB when the same pod definition is used, just with the init container removed.)

![Image]([link]

* I expect `kubelet`'s `/stats/summary` endpoint (and in particular the `memory.usageBytes` value) to only include non-terminated containers of the pod.
* I expect the pod memory usage from `kubectl top pod` and the value of kubelet's `/stats/summary`, `memory.usageBytes` to be the same, or at least close to each other.

I created a full **reproducer** with instructions here: [link]

I already did a fair bit of analysis by building Kubernetes locally and adding additional logging to what kubelet is doing.

I am pretty sure the root cause is the heuristic by which kubelet picks through the result of the [`getCadvisorContainerInfo(p.cadvisor)`]([link] call to determine whether a container is terminated. For some reason, this heuristic fails to identify the terminated init-container as terminated, and it includes its memory usage into the pods memory usage. From my understanding this is wrong, because a terminated container should not count towards a pod's memory usage.

Here is what happens in more detail:
```

---

## B11

```
kubelet memory growth: `startPodSync` `context` memory leak on every `SyncPod`

On a single-node cluster of `1.36.0-do.1` with 8-day uptime, `kubelet` process memory grows holding almost a million cancelable contexts:

`startPodSync` creates a context and stores `status.cancelFn`:

[link]

This can overwrite the previous cancelFn without cancelling it, leaking the context.

There doesn't appear to be anything that calls the `cancelFn` in the normal `SyncPod` success case.

Per [context docs]([link]

Failing to call the CancelFunc leaks the child and its children until the parent is canceled.

Stable memory usage
```

---

## B12

```
Invalid value error when creating service from exported config

**What happened**:
`kubectl get -o yaml --export` on a Service includes fields that shouldn't be exported.

**What you expected to happen**:
Resources exported with `kubectl get -o yaml --export` should be creatable without errors.

**How to reproduce it (as minimally and precisely as possible)**:
NB. Derived from [link]

**Anything else we need to know?**:
Error when running the last command: `The Service "hello-node" is invalid: spec.clusterIP: Invalid value: "<unknown>": must be empty, 'None', or a valid IP address`

Contents of the exported service config:

The `clusterIP` field is causing the error, it should be omitted when exporting config.

Exposing with --dry-run=true yields the following config:

Notably, clusterIP and nodePort are not present. My expectation is that the `--export config` would be closer to (or even equal to) the `--dry-run=true` output.

**Environment**:
- Kubernetes version (use `kubectl version`): `Client Version: version.Info{Major:"1", Minor:"6", GitVersion:"v1.6.4", GitCommit:"d6f433224538d4f9ca2f7ae19b252e6fcb66a3ae", GitTreeState:"clean", BuildDate:"2017-05-19T18:44:27Z", GoVersion:"go1.7.5", Compiler:"gc", Platform:"darwin/amd64"}
Server Version: version.Info{Major:"1", Minor:"6", GitVersion:"v1.6.4", GitCommit:"d6f433224538d4f9ca2f7ae19b252e6fcb66a3ae", GitTreeState:"clean", BuildDate:"2017-05-19T18:33:17Z", GoVersion:"go1.7.5", Compiler:"gc", Platform:"linux/amd64"}`
- Cloud provider or hardware configuration**: GKE
- OS (e.g. from /etc/os-release): Debian GNU/Linux 8 (jessie)
- Kernel (e.g. `uname -a`): Linux hello-node-3056736656-24pv9 4.4.35+ #1 SMP Wed Apr 5 13:00:57 PDT 2017 x86_64 GNU/Linux
```

---

## B13

```
Race condition in prober_manager

Ref: [link]

Prober_manager triggers a manual run of readinessProbe after startupProbe succeeds, a race condition might reset `ready=false` even after readinessProbe succeeds.
Ready state takes another success of readinessProbe to register.

#### What you expected to happen:
Ready state updates immediately after the manual readinessProbe successful run.

#### How to reproduce it (as minimally and precisely as possible):
Flake #99979

Related to #103593

#### Environment:
- Kubernetes version (use `kubectl version`):
- Cloud provider or hardware configuration:
- OS (e.g: `cat /etc/os-release`):
- Kernel (e.g. `uname -a`):
- Install tools:
- Network plugin and version (if this is a network-related bug):
- Others:
```

---

## B14

```
Excessive log generation by kubelet v1.12.2

**What happened**:
Because of the bug #69015 `kubelet` writes too many logs to syslog, producing ~5G of them per day which is filling up the rootfs very fast (and makes the whole cluster unhealthy; e.g. I have 10G of rootfs).

**What you expected to happen**:
`kubelet` produces reasonable amount of logs by default, or at least having a way to decrease this verbosity.

**How to reproduce it (as minimally and precisely as possible)**:
Upgrade `kubelet` to `1.12.2` and watch the size of `/var/log/syslog*` files every day.

**Anything else we need to know?**:

**Environment**:
- Kubernetes version (use `kubectl version`):

- Cloud provider or hardware configuration: AWS
- OS (e.g. from /etc/os-release):

- Kernel (e.g. `uname -a`):

- Install tools: `kubeadm 1.12.2`
- Others:
```

---

## B15

```
apiserver: return 4xx instead of 500 when pod runtimeClassName is empty

The Kubernetes API Server returns HTTP 500 Internal Server Error when creating a Pod whose `spec.runtimeClassName` is set to an empty string.

The following request sets `spec.runtimeClassName` to `""`:

Actual response:

The request is invalid or incomplete, but the API Server returns an internal server error.

The API Server should return a client-side error, such as HTTP 400 Bad Request or HTTP 422 Unprocessable Entity, instead of HTTP 500 Internal Server Error.

Since `spec.runtimeClassName` is invalid when it is an empty string, the error should be reported as a validation error rather than an internal server error.

1. Start a Kubernetes cluster with an affected version.
2. Start a local API proxy:

3. Send the following request:

4. Observe that the API Server returns HTTP 500:

This issue was found during RESTful API fuzzing of the Kubernetes API Server.

The request is invalid because `runtimeClassName` is empty and the Pod body is incomplete. However, this should not be surfaced as HTTP 500. It appears that an empty `runtimeClassName` is propagated to runtime class lookup logic and reported as an internal error.

This behavior is reproducible in my tests on Kubernetes v1.33.1 and v1.36.0.
```

---

## B16

```
kubelet could reject pods with NodeAffinity error due to incomplete informer cache on the node object

In our end (AKS), we observed that there is a case that kubelet could reject pods with NodeAffinty status if the node watch call got closed due to unknown reason during kubelet start up.

An illustrated procedure is (using `Tx` to indicate time):

- T1: kubelet starts, spawns the processes for registering node (create node) and node informer for syncing the node object in parallel
- T2: the node informer successfully listed empty nodes list from kube-apiserver , proceeding to watch call
[link]
- T3: the watch call stopped due to unknown issue, for instance network closed. In this case, the watch call would exit with error like:
very short watch: k8s.io/client-go/informers/factory.go:160: Unexpected watch close - watch lasted less than a second and no items received

In this case, the node informer will back-off and retry with new list-watch steps:
[link]
- T4: kubelet successfully created the node object in kube-apiserver side. Kube-scheduler kicks in and assigns pods to the node
- T5: because in T3 the list call was succeeded with empty results, the node informer had been marked as synced:

[link]
[link]
In this case, kubelet starts syncing pods and attempts to run. If these pods are set with affinity settings, the kubelet node admission check will fail the pods with "NodeAffinity" status because the node informer cache is empty. Kubelet uses a minimal node object without expected node labels for performing admission check:
[link]
- T6: kubelet node informer retry kicks in, this time it successfully synced the node object from remote. Now retried pods scheduling on this node would succeed as the node labels are expected

In our reproduction, we captured the following logs:

In the normal case, the retry back off (between T6 and T5) should be short and kubelet should not leave many pods failed.
```

---

## B17

```
Provide output of Pod-Healthcheck per API

Provide an easy way to view the detailed HTTP-response of a httpGet liveness/readyness-check of pods, in case of error 500.

This can then be used in the dashboard: [link]

If you use a web-framework with a health-endpoint like springboot or dropwizard, the endpoint will provide you with detailed information of what makes the healthcheck fail.

In case of error Kubernetes dashboard only shows a response of 500. To get the details you have to

* Have logging configured correctly which might not always be the case
* Disable the liveness-probe to be able to start the container, then call the healthcheck-endpoint yourself, where you also have to go into the container if the service is not yet setup correctly.
```

---

## B18

```
Dynamic provisioning e2e tests failing

**What happened**:
After [link] merged, dynamic provisioning tests started to panic.

Testgrid: [link]
Logs: [link]
```

---

## B19

```
Pod Failed with TopologyAffinityError because of init-container CPU NUMA Topology BUG

My Node is 250Gi memory and 64 Core CPU, which has two NUMA node, both is 125Gi and 32 Core CPU, topology policy is single-numa-node.
Create 2 pod, with init-container 1 Core CPU and 1Gi memory, app container 26 Core and 32Gi memory.
The first pod create success.
The second pod will failed with TopologyAffinityError.

Result from `lscpu`:

In `/var/lib/kubelet/cpu_manager_state` file:

Both two pods can be created successfully.
First pod use NUMA 0;
The sceond pod init-container can use either NUMA 0 or NUMA 1, but app container use NUMA 1;

1. Create one pod, which use CPU, for example 10 of 32(Numa Node) CPU of the node
2. Create another pod, which need init-container 1Core CPU, and app container need most of NUMA Node CPU, like 25 Core (greater than the left of the first NUMA)
3. The second pod will failed with TopologyAffinityError.

I think the bug is in `generateCPUTopologyHints ` function: [link]
1. when allocate init-container CPU, CPUManager will record as cpuToReuse for pod. [link]
2. before call `generateCPUTopologyHints`, get cpuToReuse of the pod, as reusable [link]
3. when caculate app container CPU, CPUManager will filter the NUMA Node which is not equal to reusableCPU's NUMA Node
4. Even if NUMA 1 is the only one that fits CPU resource acquirement, it still passed in calculating TopologyHint; NUMA 0 fits with reusableCPU, but CPU left is not enough.
```

---

## B20

```
Deployments with GCE PD fail with "...is already being used by..."

**What happened**:

From user report on [reddit]([link]

Other reports here:
* [link]

**What you expected to happen**:
Volume should attach to new node without issue.

**How to reproduce it (as minimally and precisely as possible)**:
-

**Anything else we need to know?**:
-

**Environment**:
- Kubernetes version (use `kubectl version`):
- Cloud provider or hardware configuration**:
- OS (e.g. from /etc/os-release):
- Kernel (e.g. `uname -a`):
- Install tools:
- Others:
```

---

## B21

```
Crash in AddOrUpdateTaintOnNode

Simplified PoC code is here:

and it crashed as:

###

### Relevant SIG(s)
```

---

## B22

```
Kubelet panic in syncTerminatedPod

When testing #102344 against OpenShift CI, I discovered a panic in the kubelet: [link]

Further investigation revealed that it is possible for `syncTerminatedPod` to panic under certain circumstances: [link]

We hit this case when `update.Options.RunningPod != nil` (podStatus remains nil) and `update.WorkType == TerminatedPodWork` (nil will be passed along to `syncTerminatedPod`). I'm not sure why exactly that would happen but it seems possible.

#### What you expected to happen:

Don't panic!

#### How to reproduce it (as minimally and precisely as possible):

Unclear, I've been trying to trace the code/find evidence of this happening in k8s CI but haven't found a match yet. ([link] would be nice :smile:)

#### Environment:
- Kubernetes version (use `kubectl version`):
- Cloud provider or hardware configuration:
- OS (e.g: `cat /etc/os-release`):
- Kernel (e.g. `uname -a`):
- Install tools:
- Network plugin and version (if this is a network-related bug):
- Others:
```

---

## B23

```
DRA: structured parameters: management containers

Management containers are contains that get access to some hardware while it is in use by some workload.

In terms of the "named resources" structured model that means that the resource instance is not considered "allocated" when a claim for such a management container uses it.

We would like to support this in Kubernetes 1.31, but can proceed without it.

Mostly monitoring.
```

---

## B24

```
CSI NodePublishVolume readonly is never set

**What happened**:
The `readonly` field passed to `NodePublishVolume` is never set.

In [link]

where `c` is a `csiMountMgr` object that is initialized in the `NewMounter(...)` method in [link]

Notice the `readonly` field is never set.

**What you expected to happen**:

The `readonly` field should be set to `Pod.PodSpec.Containers[x].VolumeMounts[x].readonly`

**How to reproduce it (as minimally and precisely as possible)**:
Create a CSI volume and set `Pod.PodSpec.Containers[x].VolumeMounts[x].readonly` to true.
Check the value of `readonly` in the CSI `NodePublishVolume(...)` call.
It should be true, but is false.

CC @user @user

**Anything else we need to know?**:

**Environment**:
- Kubernetes version (use `kubectl version`):
- Cloud provider or hardware configuration:
- OS (e.g. from /etc/os-release):
- Kernel (e.g. `uname -a`):
- Install tools:
- Others:
```

---

## B25

```
Support topology aware routing (node and zone)

**How to categorize this issue?**

**What would you like to be added**:
Currently there is no way to achieve topology aware routing (`kubernetes.io/hostname`, `topology.kubernetes.io/zone`, `topology.kubernetes.io/region`) and define _deterministic_ rules like the ones offered from the already deprecated and removed [`ServiceTopology`]([link]
- Prefer endpoints on the same node, fall back on any available endpoint if none are available for this node: `["kubernetes.io/hostname", "*"]`.
- Prefer enpoints on the same zone, but fallback on any available endpoint if none are available within this zone: `["topology.kubernetes.io/zone", "*"]`.
- Prefer endpoints on the same node, fall back to endpoints in the same zone, followed by the same region, and failing otherwise: `["kubernetes.io/hostname", "topology.kubernetes.io/zone", "topology.kubernetes.io/region"]`. This may be useful, for example, in cases where data locality is critical.

The `ServiceTopology` feature was deprecated (and removed in K8s 1.22) in favor of [`TopologyAwareHints`]([link]
Note: This feature, specifically the alpha topologyKeys API, is deprecated since Kubernetes v1.21. Topology Aware Hints, introduced in Kubernetes v1.21, provide similar functionality.

Although that the docs write that TopologyAwareHints "provide similar functionality", this is not reflecting the reality. TopologyAwareHints is a feature that is applicable only in particular use cases and is not a replacement for the feature offering of ServiceTopology.

Drawbacks of TopologyAwareHints:
- Sometimes the CPU-balance heuristic is wrong. For example, if we know that the whole zonal CPU pool does not model the set of clients which will access a service, then we may erroneously disable hints. (ref [link]
- Hints do not work at low-endpoint counts. (ref [link]
- Hints are not deterministic.
- ...
```

---

## B26

```
[KEP-2400] Determine a set of metrics for measuring node performance with swap enabled

Determine a set of metrics for node QoS in order to evaluate the performance of nodes with and without swap enabled. We want to also better understand relationship of swap with memory QoS in cgroup v2 (particularly `memory.high` usage).

This issue does not require any code changes. We welcome outside feedback and test results.

See [link]
```

---

## B27

```
E2E Proposal: Verify tcpSocket property of v1.Probe along with success and failure threshold.

**What would you like to be added**:
A E2E to verify `core.v1.tcpSocketAction` resource along with probe's important properties like `successThreshold`, `failureThreshold`, and `periodSeconds`.

Note: following default values are in effect `delay=0s timeout=1s period=10s #success=1 #failure=3`

**Why is this needed**:
To improve API coverage based on [label] and their important properties.
[link]

E2E behavior could be:
Create a pod with a container having `tcpSocket` based readiness and liveness probes provided with successThreshold, failureThreshold and periodSeconds values and container should not accept any connection after ~30 sec of it's start. Container MUST be ready after `successThreshold * periodSeconds` (<~30s) is reached. Container MUST NOT be in ready state after `failureThreshold * periodSeconds` (>~30s) is reached.

Note: May need to implement connection closing mechanisam at certain time for `gcr.io/kubernetes-e2e-test-images/liveness:1.1` image to test failureThreshold for `tcp` requests.

[team]
```

---

## B28

```
CRI: support non-builtin container runtimes

The built-in cri-docker integration relies on some legacy support (e.g., the docker-cadvisor integration) that a new CRI integration does not have. Below is a list of issues we need to address to fully support a non-builtin, non-docker container runtime via CRI.

A (potentially incomplete) list of issues to unblock adopting a (non-docker) CRI integration.
- [x] Refactor kubelet to consume container metrics from CRI: #46984
- [x] Refactor kubelet to consume image filesystem stats from CRI: #33048
~- [ ] Providing cgroups for kubelet/cadvisor to track resource usage of CRI shim and container runtime stats:~ (see update in #30702)
- [ ] Authentication for the streaming server: #36666
- [x] Improve log format to handle logs: #44976
```

---

## B29

```
kubectl get svc could show truncated hostname for Service.Type=Loadbalancer on AWS

Dear all,

I was following the Guestbook example on aws, when I do step seven

The output column for External_IP is simply empty. Is this already reported to do with k8s or it's my setting up of aws wrong?

Best,

Dong
```

---

## B30

```
The CNI binary used by salt will leak iptable rules

I am testing rktnetes on gce using the kubenet with the CNI binary downloaded from [link]

And I am seeing iptable rule leaks issue. I am pretty sure the CNI binaries we used [here]([link] doesn't contain the fix.

Ref:
[link]
[link]

cc @user @user [team] @user
```

---

## B31

```
Multiple concurrent docker image pulls may lead to layer corruption

When adding a new node to an existing cluster (k8s 0.19.3), all containers scheduled on this node fail to start with the following pod event log:

All subsequent container restart fail with the following error (also mentioned in #7332)

When this starts happening Docker fills the local disk indefinitely at a rate of about 4GB/minute with only 4 scheduled containers.
```

---

## B32

```
Expose container's own identity to the container

Container can be identified in the cluster at a given point of time by a tuple `(namespace, pod_name, container_name)`. Currently, the only guaranteed way to get this information is Downward API, which requires quite lengthy definition in the container's spec.

However, this information is extremely important for monitoing/logging client libraries. They would benefit from being able to out of the box send the information to the backend without querying Kubernetes API or a separate agent. Example issue: [link]

[team]
```

---

## B33

```
Memory Eviction Memcg notifications are not effective.

While debugging [link] we found that despite memcg notifications waking up the eviction manager, the eviction manager was unable to take action before a system oom ~6 seconds later. The following sequence of events occurred:
1. Memory threshold crossed.
2. Memcg notifications triggers synchronize call in eviction manager
3. Eviction manager gets summary stats (~10 seconds old)
4. Eviction manager determines there is no pressure (because stats are old)
5. Repeat steps 1-4 a couple times (for ~6 seconds)
6. System OOM

cc @user @user @user @user @user
```

---

## B34

```
Device manager silently fails to restore checkpoint after upgrading to 1.20+

After upgrading kubelet from version <= 1.19 to version >= 1.20, the device manager will fail to restore its state from the checkpoint. The change was introduced in [link] .

The restore fails silently (it actually writes a warning in the logs, but keeps going). Because of this the device manager state is inconsistent up until the device plugins register themselves again, which can take minutes, depending on the specific device plugin. We seen up to 5 minutes on real clusters the for SRIOV device plugin.

Because of the inconsistent state, the kubelet will **NOT** update the device availability to zero, so the scheduler will send pods towards the inconsistent kubelet.
At admission time, the device manager allocation will not trigger, again because of the incosistent state, so pods will be admitted without device plugins actually being allocated to them.

#### What you expected to happen:
Any of the following wouls be acceptable
1. the kubelet recovers the checkpoint state correctly
2. the kubelet sets its own state as inconsistent, so pods aren't scheduled until the node heals
3. the kubelet sets its own state as inconsistent, so pods aret scheduled, but aren't admitted until the node heals

#### How to reproduce it (as minimally and precisely as possible):
1. run pods requesting devices on <= 1.19 kubelet
2. drain the node
3. upgrade the kubelet to a version >= 1.20
4. run pods on the upgraded node typically as soon as the node gets Ready

The issue was discovered first in openshift, but turns out is not openshift specific.

The bug triggers only after a upgrade, so kubelet is stopped, updated (<= 1.19 to >= 1.20) and started again.
There are no more know ways to trigger this bug.

The updated kubelet fails to restore the checkpoint data. See this excerpt from the logs

The kubelet keep going, but this means the internal devicemanager maps will be **completely** empty.
```

---

## B35

```
GCE PD Detach fails if node no longer exists

**Problem:**

If a node with a GCE PD attached is deleted (before the volume is detached), subsequent attempts by the attach/detach controller to detach it continuously fail, and prevent the controller from attaching the volume to another node.

**Repro steps:**
1. Create a pod referencing a GCE PD
2. Wait for pod to get scheduled and running.
3. Delete the node VM (using gcloud) that the pod is scheduled to.
4. Check if volume is detached by attach/detach controller:
- _Expected:_ Volume detached.
- _Actual:_ Volume continuously fails detach.

**Logs:**
<details>
From `/var/log/kube-controller-manager.log`:

</details>

**Workarounds:**
- Restart the kube-controller-manager binary on the master.

-or-
- Recreate a node with the same name.

**Proposed Fix:**

If GCE PD detach fails with `instance not found`, assume successful detach.
```

---

## B36

```
kube-controller-manager stuck on updating node status

**What happened**:
During controller-manager startup it spends ~13 minutes trying to updating the node status (On a 5 node cluster)

During this time it's not processing DaemonSets etc.

**What you expected to happen**:
To complete this phase quickly

**How to reproduce it (as minimally and precisely as possible)**:
Unknown

This is happening during a self-hosted cluster update (i.e. all of the VMs being destroyed/created in sequence)

**Anything else we need to know?**:

It starts going wrong here:

[controller-manager.txt]([link]

**Environment**:
- Kubernetes version (use `kubectl version`):

- Cloud provider or hardware configuration**: Openstack
- OS (e.g. from /etc/os-release):

- Kernel (e.g. `uname -a`):`Linux kubernetes-kubernetes-zone2-0-1503077970 4.9.24-coreos #1 SMP Wed Apr 26 21:44:23 UTC 2017 x86_64 Intel Xeon E3-12xx v2 (Ivy Bridge) GenuineIntel GNU/Linux`
- Install tools: custom
- Others:
```

---

## B37

```
Printing CLI parameters for Kubelet is misleading to users.

While working on [link] I ran into an issue where the CLI was reporting that `--fail-swap-on="true"`. But in the code it was actually set to "false". This is because the flag was set in the KubeletConfig.

We have users also noticing that the logs in Kubelet for CLI don't report the actual value as they are actually being read from the KubeletConfig.

We should bring the values of these configurations that they are rather than the CLI fields.

Log at logs for a CLI parameter (swap, eviction, etc) and change those values in the KubeletConfig.

Kubelet logs will display the CLI parameter rather than the KubeletConfig value.

[link]

CLI parameters are deprecated and replaced for KubeletConfig but I'm not sure if we bring the actual values in the logs.
```

---

## B38

```
"kubectl logs --follow" has not printed new logs after log rotation.

When running `kubectl logs pod-name --follow`, new logs are not output to the logs command after the log file has grown and rotated.

Even after log rotation, new logs are output to `kubectl logs pod-name --follow`.

The following steps will reproduce it.

1. Deploy a Pod that continues to output to stdout.
2. Run `kubectl logs pod-name --follow`.
3. Wait a while and the log file will be rotated. The waiting time depends on the environment.
4. New logs will not be output to logs command.

The sample pod is following.
```

---

## B39

```
Probe timeout ignored by ExecAction

I'm using a readiness probe that may take a long time to run, and I expected it to be interrupted after the specified timeout.

A probe defined like this:

Instead of timing out and failing, it is actually succeeding and ignoring the timeout.

I noticed that both `TCPSocketAction` and `HTTPGetAction` probes timeout according to the value of `TimeoutSeconds`, `ExecAction` on the other hand ignores it.

Looking at the code:

`if p.Exec != nil`, no reference to timeout:
[pkg/kubelet/prober/prober.go#L146]([link]

`if p.HTTPGet != nil || p.TCPSocket != nil`, timeout is used:
[pkg/kubelet/prober/prober.go#L163]([link]
[pkg/kubelet/prober/prober.go#L171]([link]
```

---

## B40

```
Pods that are using host network should still be accessible to other pods via the API semantics

We realized just recently that HostNetwork pods aren't given a pod IP. I wanted to get agreement on how we can make that pod visible.
1. The effective ip of the pod is the host ip (which we also set).
1. We could set podIP to hostIP when in host networking and all higher level components would work
2. We could change higher level components like the endpoints controller to look at hostIP instead of podIP in this case
2. The pod should get an ip assigned by the network plugin, but the network plugin makes the decision

We could do both of the above. i don't know that we've formally stated hostIP is the internal cluster IP - because podIP is guaranteed to work in the cluster I think we would have to formalize that.

I'm looking for a quick decision (if possible) on whether 1.1 or 1.2 are acceptable - if they are, we are considering carrying a patch.
```

---
