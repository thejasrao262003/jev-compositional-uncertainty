# Kubernetes blinded leakage read, repeated after Amendment 4 (40 cleaned issues, new seed)

**Who:** by the authors' decision (Amendment 5), an AI assistant, the
same kind of read as the first one. It must not be the assistant that
wrote the cleaning rules.

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
Kubelet doc.go

I think we should write doc.go files for packages in Kubelet, like we do for the rest of Kubernetes. In some cases, it's not obvious what the code in a package does (for example, without spending some time reading the code, it's not clear what kind of "container" files are in kubelet/container - some "container" source files are outside the folder). In some cases, I think the doc.go files need to be expanded upon (kubelet/types/types.go says "Common types in the Kubelet.", but there's also a kubelet/types.go file).

I think having clear doc files will help structure the code better - contributors will know how they should organize their code when introducing a feature.
```

---

## B02

```
Each time a pod exits, kubelet cpu usage increases with cgroups v2

When a pod exits, there is some problem in the cgroup cleanup. The containerd cgroup within the kubelet cgroup does not get deleted, and then the kubelet keeps trying to delete the kubelet cgroup, which fails because of the child cgroup. The kubelet continues to try to delete the cgroup every 1 second or so. As pods start and stop, the number of cgroups in this state grows, and the kubelet process itself gradually consumes more and more cpu, until it gets to 100% of available.

Here are snippets of the /var/log/syslog for a single example. This is for the case of kubelet cgroup /sys/fs/cgroup/kubepods.slice/kubepods-burstable.slice/kubepods-burstable-podde737447_24b2_4f9e_a805_ad1161a169fb.slice which contains a sub-cgroup cri-containerd-67620447e632a1b3edb19fe05a2b44211cffb996bf6ba5ff52811a8bf32eb8b7.scope.

First, logs of the containerd startup/shutdown:

After this, the following logs keep appearing over and over again:

Not use 100% cpu

Not sure
```

---

## B03

```
liveness/readiness probe is executed and failed while pod is terminated

liveness/readiness probe fails while pod is terminated. Also it happened only once during the pod termination. The issue started happening after upgrading version to v1.7 from v1.6.X
execute `kubectl delete pod nginx-A1` to delete pod, so status of the nginx-podA1 is changed to `Terminating`, right after that it seems Liveness and Readiness Probe is executed and failed, but only once.
Nginx reverse proxy is running in the pod. so I just use `httpGet`method for liveness and readiness

Here is my Deployment config.

Here is Events log by `kubectl describe pod nginx-A1`
```

---

## B04

```
Expose kube-proxy metrics on 0.0.0.0

We'd like to change the Kube Proxy MetricsBindAddress default from 127.0.0.1 to 0.0.0.0.
Currently the kube-proxy metrics are exposed by default on 127.0.0.1 interface. It makes it impossible to export kube proxy metrics to prometheus server via prometheus operator.
I've sent [link] to change the bind address in tests, but we believe that changing the default might be actually a better idea.

Other components (e.g. [kube-scheduler]([link] use 0.0.0.0 as the default metrics bind address.

<br />
I'm happy to send a PR to do that, but would like to get your opinion first.
```

---

## B05

```
RuntimeHandlerResolver: interface invalid nil checking

the nil checking for interface RuntimeHandlerResolver in #L109 will never check whether the underlying struct is nil.
A reflect nil checking is needed to avoid panic in running 'rcManager.LookupRuntimeHandler'(#L111)
[link]

Add reflect nil checking for rcManager

1. kubelet enable standaloneMode
2. pod.Spec.SecurityContext not nil
```

---

## B06

```
[KEP-4191] Support case when writeable layer and readable layers are on same mount but in different locations

In KEP-4191, we wanted to support a case where writable layers and readonly layers are on a separate disk.

This works fine but we found a bug if these layers are on the same disk but in different locations.

You can reproduce this by setting `graphRoot` and `imagestore` in crio storage to different locations.

Kubelet should react to container storage configurations.
```

---

## B07

```
Node e2e serial local storage capacity isolation tests are failing

[link]

Example failure: [link]

Pods that should be using less than their limits are being evicted for exceeding them. These tests were passing before being moved to the serial suite from the flaky suite.

The only thing I can think of off the top of my head is that the GPU test adds something to containers that takes disk space.
cc @user is that a possibility?
```

---

## B08

```
CRI: Implement container log rotation

TL;DR: We want to allow kubelet to rotate the container stdout/stderr logs, and add a CRI call to ask the runtime to reopen the log file.

kubelet decides the log directory structure and passes to the runtime the path where container log should be stored. Given the level of knowledge and control kubelet has, it is currently the best candidate to rotate the logs (vs. runtime or a separate daemon). The detailed evaluation is in the [proposal doc]([link]

IMO, the initial version should target a simple policy of size limit per file. We can iterate and add more advanced features based on disk management in the future. The stretch goal for this release will be supporting reading logs (`kubectl logs`) from rotated log files.

As for the docker integration (i.e., `--container-runtime=docker`) that does not fully implement CRI logging, kubelet should skip log rotation.
```

---

## B09

```
Containers within a pod don't share the same UTS namespace

During reviewing container runtime interface proposal, I surprisingly found that containers within a pod today only share both network and IPC namespace, not uts one. I don't think there are any production issues caused by this, but we should clean up this.

cc/ @user @user
```

---

## B10

```
pod logging broken with journald logging driver

Warning starting pod when using the journald docker logging driver

This breaks container-level logging

@user
```

---

## B11

```
Graceful Node Shutdown should allow admission of high priority pods

[Graceful Node Shutdown feature]([link] terminates pods in two stages: critical and non-critical pods. It is possible to specify a specific deadline for each of these stages.

Terminating workloads on a node can take considerable amount of time.

Critical workloads (e.g. CSI driver, networking, monitoring, etc.) can terminate before the normal pods are terminated. This can happen for example during a DaemonSet rollout. Such disruption can have detrimental effect on the graceful termination of lower priority workloads.

[Pod Priority Graceful Node Shutdown]([link] also introduces a way to describe multiple termination stages according to arbitrary priorities. Allowing gradual admission could be useful there as well.

This also causes race between the daemonset controller and kubelet which has been discussed in [link]

Critical priority pods (e.g. `system-node-critical`, `system-cluster-critical`) should still be admitted during GNS until it is their turn to terminate.

Node taints should also reflect this situation, either by removing

or adding a custom taint for Graceful Node Shutdown that controllers can work with (e.g. daemonset controller) and add a default toleration. This is already an existing pattern:

[link]

Create a critical priority pod when `shutdownGracePeriod` is in effect.

Currently the pod is rejected with:
```

---

## B12

```
When containers use memory backed tmpfs and hit a OOM limit they will keep OOM on restarts.

While aiming to promote SizeMemoryBackedVolumes to stable, tim brought up a point about what would happen if a pod that hit a OOM due to tmpfs memory limits would keep OOM as the pages are still kept around.

He is correct. If a pod hits a OOM limit with tmpfs it will keep OOM and never purge that memory

I would expect the tmpfs to be empty on a restart of the container.

I used kind 1.30.

kubectl exec -it example -- sh
cd /dev/shm/
dd if=/dev/zero of=filename bs=1024 count=2GB
command terminated with exit code 137

In this case, the pod is unable to start again and it gets stuck with:

This is probably a long outstanding issue so its unclear if this will be fixed as a bug.
```

---

## B13

```
[SIG NODE Discussion] Metrics and dashboards for monitoring SIG-Node CI test failures and bug triage health

### Context
In the recent SIG-Node CI subgroup meetings (6/10/2026), we discussed the need to better track our CI stability and test degradation over time.

Currently, we are manually tracking the status of our Testgrid dashboards in a [Spreadsheet Tracker]([link] before every meeting. We document the current status (Passing/Flaky/Failing) of the jobs and link them to tracking GitHub issues, but doing this manually makes it hard to see historic data and trends.

### Goals
We would like to gather community input on what metrics, tooling, and dashboards we should use to automate this monitoring. For starters, we can try to answer questions like:
* How long has a specific test or job been failing?
* Is a recurring failure caused by the same error or a new regression?
* How long do SIG-Node CI bugs remain open?
* How many `important-soon` bugs do we currently have, and what is their average resolution time?
Please recommend any more you think of, open to all suggestions!!

### Existing Efforts & Ideas
* We dug up an [existing dashboard started by dims]([link] but we need to determine how persistent this data is, how it's generated, and how we can best utilize or adapt it.
* Could we leverage existing Kubernetes `test-infra` tooling (like BigQuery metrics/[Kettle]([link] `k8s-triage` in the [aggregated failures dashboard]([link] to automate the data we currently put in our manual spreadsheet?

### Call to Action
We are opening this issue to invite ideas from the CI/CD community.
1. What metrics do you think are most important for us to track?
2. Are there existing dashboards or tools in the Kubernetes ecosystem we should be leveraging?
3. Any volunteers interested in helping build out or maintain this reporting?

Please drop your thoughts and suggestions below!

cc: @user
```

---

## B14

```
Incorrect PodMemory usage after container termination

PodMemory metric continued to be available for few minutes after pod was removed from the node.

PodMemory metric should have been removed from the old pod instance as soon as new pod was destroyed or new pod was created.

From initial understanding, kubelet/cAdvisor housekeepingInterval seems to be the static interval at which housekeeping should occur. If allowDynamicHousekeeping is enabled, cAdvisor determines the actual housekeeping interval based on houseKeepingInterval and maxHousekeepingInterval as shown in [manager/container.go#L481C1-L505C2]([link] with some jitter.

Need to understand the behaviour of [statsCacheDuration]([link] and maxHousekeepingInterval when kubelet is restarted. Does kubelet dump the cache data to disk before the package upgrade?

Moreover, since these maintenance are happening for kubelet upgrades, does time to upgrade and bootstrap kubelet could lead to additional delay in housekeeping. One more weird observation I could find is, node uuid has changed twice, once while upgrading at 11 AM(which is relevant for this issue) and then again at 2 PM(which is unrelated).

<img width="1600" height="959" alt="Image" src="[link] />

This was observed during kubernetes upgrade.
Node was drained and kubelet was upgraded.

**Context**
In case of Kubernetes Upgrade related maintenances, pods are rescheduled or temporarily evicted from the node. It has been observed that the newly formed pod consumes approximately double the memory of the original pod at startup. Multiple alerts are raised due to this as it can violate set alerting thresholds.

Below is the original query raising PodMemory alert for workload. We can notice the query is granular at pod level.

From the graph view, we can see a sudden spike in memory usage before 11 AM when the pod got rescheduled.
```

---

## B15

```
DRA-backed extended resources do not report ResourceHealthStatus in PodStatus

When a Pod uses an extended resource backed by Dynamic Resource Allocation, kubelet prepares the generated special ResourceClaim and injects the CDI devices, but it does not populate `pod.status.containerStatuses[].allocatedResourcesStatus` for those resources.
﻿
For DRA-backed extended resources, the container request is in `container.Resources.Requests`, not in `container.Resources.Claims`, so the health status update path never considers `pod.Status.ExtendedResourceClaimStatus.RequestMappings`.
﻿
As a result, DRA-backed extended resources can be prepared and passed into the container, but their health is not reflected in PodStatus.

When `ResourceHealthStatus` is enabled and a DRA plugin reports health for a device allocated via a DRA-backed extended resource, kubelet should publish that health in `pod.status.containerStatuses[].allocatedResourcesStatus`.
﻿
The reported status should correspond to the generated special ResourceClaim and request from `pod.status.extendedResourceClaimStatus.requestMappings`.

N/A.

N/A.
```

---

## B16

```
GracefulNodeShutdown produces multiple “ContainerStatusUnknown” pods if the node is shut down with pods having not-ready tolerations

When having pods that have the following toleration:

Shutting down the pod's node configured with GracefulNodeShutdown will leave a number of replicas of the pods in a `ContainerStatusUnknown` status after restarting the node where the pod originally was.

According to `kubectl get po -w`:

I was expecting that there will be no pods with `ContainerStatusUnknown`.

Minimal Env:
1 Cluster with 1 control plane and 1 worker node

Reproduction:
1. Enable GracefulNodeShutdown feature in your node.

2. Create the following Deployment:

3. Create the deployment

4. Reboot the worker node (in this example, localmachine2.localdomain)

5. Wait for a few minutes until the node shuts down and starts up again.
6. Check the pod list
```

---

## B17

```
kubelet: Device plugin fails to connect to new instance of plugin if previous one is terminated

The kubelet fails to connect to the device plugin if a previously running device plugin was running on the node with the same resource name.

Kubelets can get into a situation of running two pods advertising the same device plugin for a brief short period of time. For example, consider the following situation of a vendor hypothetically "upgrading" the device plugin:

1. kubelet runs`first-device-plugin` advertising resource `example.com/resource`
2. device vendor upgrades device-plugin to `second-plugin` and user deploys it
3. kubelet switches to use `second-device-plugin` advertising resource `example.com/resource`
4. user deletes `first-device-plugin`

Prior to v1.25.0, kubelet would handle this situation, and on step 4, disconnect of `first-device-plugin` would ensure that `first-device-plugin` would be disconnected, and maintain connection to `second-device-plugin` (since it was most recently connected).

This regressed as part of [link] where as part of the deletion of the `first-device-plugin` (step 4), kubelet would disconnect from "the most recently" connected plugin, namely `second-device-plugin`, and thus would get into a situation where neither the first or second device plugin would be connected. This would result in kubelet failing to adverting resources for the device. This is because of a bug where kubelet only stores the state of the most recently connected plugin and on disconnect, disconnects the most recently connected plugin.

I expected kubelet to either maintain the same behavior as pre 1.25: when deleting a device plugin pod, to disconnect from the device plugin that was deleted rather then the most recently connected plugin.
```

---

## B18

```
The allocatable and capacity values ​​for "ephemeral-storage" under node.status are not displayed in the same format.

I'm checking the status of a node and noticed that the base of the **"ephemeral-storage"** field in the allocatable and capacity fields is inconsistent. The "ephemeral-storage" field under allocatable is in **binary format**, while the "ephemeral-storage" field under capacity is in **decimal format**. Is this intentional or a bug?

<img width="2346" height="162" alt="Image" src="[link] />

I think they should be in the same format.

kubectl get node xxx -ojsonpath='{.status.allocatable}'

kubectl get node xxx -ojsonpath='{.status.capacity}'

Then, compare them.
```

---

## B19

```
DRA: allocator should fail closed (per-node) on a malformed ResourceSlice nodeSelector term count

Follow-up to #141212 and #141213. The validation fix in #141213 stops a new or modified ResourceSlice from carrying a per-device `nodeSelector` whose term count is not exactly one. It ratchets the new constraint, so a slice with a multi-term selector that was stored before the fix, or accepted by an older API server during a version-skewed rolling upgrade, is still admitted on an unchanged update.

Those already-stored multi-term slices can still reach the structured allocator. `createNodeSelector` handles the term count like this:

- `len == 0`: no-op. This is not reachable through a normal allocation. `ValidateNodeSelector` already rejects a zero-term selector ("must have at least one node selector term"), and even a stored one matches no node, because `nodeaffinity`'s `Match` returns false when there are no terms, so `isSelectable` filters the device through `NodeMatches` before `createNodeSelector` runs. Rejecting zero terms here would be defense in depth, not a fix for a demonstrated available-everywhere allocation.
- `len == 1`: merged.
- `len > 1`: returns `fmt.Errorf("unsupported ResourceSlice.NodeSelector with %d terms", ...)`.

The `> 1` error is not wrapped with `internal.ErrFailedAllocationOnNode`, so the DynamicResources Filter plugin treats it as a framework error rather than an `Unschedulable` result for that node. A framework error from Filter cancels the remaining node search and aborts the scheduling cycle, and it recurs on retry while the malformed slice stays in place. #141212 has a v1.36.2 reproducer.

There is also an ordering edge. `createNodeSelector` returns as soon as it sees a result with a `nodeName`, so a multi-term selector on a device that appears after a `nodeName` device is never inspected, while the same selector before it returns the hard error. Whether a malformed slice aborts the cycle therefore depends on result order.
```

---

## B20

```
kubelet will never terminate a pod if image registry is unavailable for a pod container

After an unbelievable amount of time debugging the following this past week:

[link]
[link]

I discovered that I could reliably cause the `kubelet` to never delete a pod that was `Terminating` if the pod had never been started correctly because the docker image pull returned a `RegistryUnavailable` error.

I verified this by modifying the kubelet to always return `RegistryUnavailable` for a particular image name. I then created a namespace, added a replication controller that referenced the image, and then watched as the pods got stuck in "Waiting" state but never actually reported a reason. I then deleted the namespace, and was able to see that in-fact the `kubelet` never properly handled the `terminated` response.

I was able to fix this issue by modifying:

[link]

to return `ErrImagePull` when the repository was not available. This change resulted in letting my `kubelet` properly terminate the pod. I think this is the correct behavior to not special case `RegistryUnavailable` since in many cases the registry may never become available (its most definitely not a temporary situation).

I suspect this is the potential source of a number of instances of the namespace failed to delete flake because pods remained.
```

---

## B21

```
After replication controller is deleted, some nodes do not kill running containers

Discovered this while debugging with @user

Some nodes do not kill containers after associated replication controller is deleted.

**Repro steps:**
- You may use a standard GCE 4 node cluster `n1-standard-1 (1 vCPU, 3.8 GB memory)`
- Download [sleepypod.yaml]([link]
- It defines a replication controller with 300 replicas with 10 containers per pod using a _tiny_ container which contains a statically compiled C program that just starts up and goes to sleep for a very long time.
- Execute `./cluster/kubectl.sh create -f sleepypod.yaml` to create the replica controller
- Execute `./cluster/kubectl.sh describe rc sleepypod` repeatedly to check how many pods are scheduled.
- Monitor `Pods Status`
- Wait until the number of scheduled pods stops increasing (depending on the size of your cluster, you will not be able to schedule all 300 replicas, that's ok).
- Call `./cluster/kubectl.sh delete -f sleepypod.yaml` to delete the replica controller
- Call `./cluster/kubectl.sh get pods` verify there are no `sleepypod-...` in the response
- SSH into each node machine and execute `sudo ps | grep sleepy`

**Expected result:**
- All nodes should have no running `sleepypod-...` containers

**Actual result:**
- One or more nodes will not terminate the `sleepypod:` and associated `pause` containers running on it:

Restarting kubelet (`service kubelet restart`) or restarting docker causes the running containers to all get killed.
```

---

## B22

```
Deduplicate NFS server containers

There are two NFS server containers in the kubernetes code:
- [kubernetes/examples/volumes/nfs/nfs-data/Dockerfile]([link]
- [test/images/volumes-tester/nfs/Dockerfile]([link]

Instead of maintaining both (nearly identical), I propose removing the `examples` version and having the NFS example point to the `test` version.

CC [team] @user/rh-storage
```

---

## B23

```
When external source IP matters

I have not found any documentation describing scenarios where the external source ip of the routed pods matter.

I want to kuberialize our SMTP servers using a service and a replication controller. Problem is that the world expect these servers to communicate from a specific external ip.

Is it a "right way" of doing this? I will contribute a .md for this scenario if I find the right solution :)
```

---

## B24

```
Determine whether we should continue to require UID in node config source reference

#### Reposted from [link]

This has been a requirement of dynamic Kubelet config since the original proposal, to require users to be completely explicit (time and space) about which ConfigMap to use. If the UID in the config source doesn't match the UID of the ConfigMap, the Kubelet currently rejects it.

IIRC there were concerns along the lines of ConfigMaps being deleted and recreated with the same name but different content... though this is less of an issue today now that we have the --append-hash option in kubectl (obviously the potential for in-place ConfigMap mutation still exists, but if users are using --append-hash I wouldn't expect them to mutate the ConfigMap after creation).

The Kubelet also checkpoints by UID, so it was convenient to already have this specified in the object ref, though I guess if we relaxed this requirement it could just resolve the UID and stick it in the local copy of the config source when it first downloads the ConfigMap.

I can't remember other reasons to require UID, if any.

---

A massive downside of requiring the UID is that you cannot fully-statically-specify the configuration of a cluster; the UID is assigned by the API server at creation time.

This *must* be resolved before dynamic Kubelet config ([link] goes beta.
```

---

## B25

```
DRA resource claim controller: fails to clean up deleted ResourceClaims on startup

* kube-controller-manager is stopped.
* A allocated claim with one pod in ReservedFor is marked as deleted (but not removed yet because of the finalizer).
* That pod gets deleted, terminates and gets removed.
* kube-controller-manager is restarted.

The ResourceClaim controllers logs:

It does not do anything, so the claim remains pending.

This was triggered while working on upgrade/downgrade scenarios.

The ResourceClaim controller should remove the pod from ReservedFor, the allocation, and the finalizer, thus unblocking the removal of the ResourceClaim.

Not easy, needs WIP test.

This is a regression introduced by [link]

The logic here is inverted:
[link]

The correct expression is `deleted := newObj == nil`.

This causes the enqueuing of the claim for processing to get skipped in

[link]

Normally, this gets mitigated by pod removal which also has the desired effect, but in this particular case that removal is never observed - the pod is already gone when the kube-controller-manager starts.
```

---

## B26

```
Liveness probe failure container restart leads to container starting up with started=true and liveness probes starting before startup probes have run

The full details of the repro can be seen in the Bash script below, but roughly:

1. Start a container with startup and liveness probe.
2. Wait for both to succeed. All normal so far.
3. Flip liveness probe to fail.
4. Container restarts.
5. New container sees liveness probe before startup probe.

I would expect the new container to first need to pass its startup probes before liveness probes begin, as per the docs here: [link]

Reproduction bash script:

Save as repro.sh and here are the results of me running it:
```

---

## B27

```
kubelet crash loop panic with SIGSEGV

I was running some pods on my node as usual.
At some point (23:41:35.127989 in the log), the kubelet crashed and then went into a crash loop.

Log showing the first crash and several thereafter: [kubelet-crash.txt]([link]

The errors I see shortly before the crash are:

Stack trace from the first crash (later stack traces are a bit different):

Ideally no crash, but at least a useful error message.

Really not sure.
```

---

## B28

```
Timeout waiting for systemd to create kubepods-burstable-***.slice

When I **frequently** increase and decrease the **replica count** (with python api)to adjust the number of pods over a period of time:
![image]([link]

The cluster **cost some more** memory but with the same count of services(and pods), and at this point, continuing to adjust replicas will result in a significantly longer time (possibly even more than **600 seconds**, normal is 1.5-3s) required for creating new pods.

As title: Timeout waiting for systemd to create kubepods-burstable-***.slice
![image]([link]

And also: Timed out while waiting for systemd to remove kubepods-burstable-***.slice
![image]([link]

normally start new pod without timeout
![image]([link]

frequent replica adjustments (roughly over 500 times within 15 hours, **up to 40 one by one and reduce to 1 one by one**) for a same service, use python api

I continuously adjust the replica count using a Python program. Under normal circumstances, the startup time of pods is shown in the left graph (where the left side represents the pod count, and the right side represents the startup time of new pods). However, after an extended period of frequent replica adjustments (roughly over 500 times within 15 hours), the duration is shown as depicted in the right graph.
**Even Kubernetes' API timeouts in the end.**
![image]([link]
```

---

## B29

```
Remove docker references in pod_worker_test.go

We should not be testing docker-specific logic outside of docker package. pod_worker_test.go still imports go-dockerclient directly and uses a fakeDockerClient. They should be replaced with the generic FakeContainerRuntime, etc.
```

---

## B30

```
Add e2e test(s) for volume scheduling limits

Right now, we have e2e test for [volume scheduling limits]([link] that executes only CSI mock driver with artificial limit of 2 volumes per node.

We need a test with real CSI driver(s).

Proposal:

* Allow individual test storage drivers to specify if they support CSI limits.
* Add a test that picks a random node and creates as many pods with a PV that the volume can handle (128 on GCE!).
* Check that the node can't handle any other volume.
* Make this test part of [CSI external test suite]([link]

* Add similar test(s) for in-tree volume plugins.
* Make sure the tests work with in-tree volume plugins migrated to CSI.
```

---

## B31

```
PersistentVolumeController should not hardcode recycler image

The recycler pod image used by the NFS & HostPath persistent volume plugins is hardcoded to `gcr.io/google_containers/busybox`, here:
[link]

There are several problems with this approach:

1. No way to run a deployment off a custom repository. E.g. if an organization wanted full control of every image running in their cluster.
2. The hardcoded image is unversioned, meaning there is no way to ensure you're getting the latest version (and if latest is updated, there is no way to safely roll out the updates).
The image, repository & tag should be configurable at deployment time, e.g. with a command-line flag. The default image should use a versioned tag (not latest).
```

---

## B32

```
DRA: detect stale DRA plugin sockets

@user observed that after uninstalling his DRA driver *without* removing the Unix Domain socket used for gRPC towards the kubelet, kubelet didn't unregister the driver. We may have to add some liveness probing to `pkg/kubelet/cm/dra/plugin/registration.go`.

The kubelet needs to remove ResourceSlices on behalf of a defunct DRA driver.
```

---

## B33

```
Remove deprecated built-in CSI RBAC roles in 1.17

The built-in `system:csi-external-provisioner` and `system:csi-external-attacher` cluster roles here
[link]

are deprecated in 1.13
[link]

when this issue was resolved: [link]
```

---

## B34

```
Move dockershim code into a separate CRI

We currently have a flag `experimental-dockershim` in kubelet here:
[link]

Backed by the code here:
[link]

There is a `TODO` as well:
[link]
```

---

## B35

```
kube-proxy pods are not getting deleted after grace period

I have an ordinary GCE e2e cluster running on flannel (NETWORK_PROVIDER=“flannel”). After starting the 500 Node cluster some kube-proxy pods are pending (I've seen 1 and 3) with "ErrImagePull" errors. I tried to delete them normally (`kubectl --namespace=kube-system delete pod kube-proxy-blablabla`)

and waited for 10 minutes.

In the end I had to force deletion (`kubectl --namespace=kube-system delete pod kube-proxy-blablabla --grace-period=0`) which worked.

cc @user @user @user @user/goog-node

Assigning to @user to reassing.
```

---

## B36

```
[Sidecar Containers] Eviction message should account for the sidecar containers

The `evictionMessage` is not accounting for the restartable init containers (sidecars).

When pod is evicted, requests of the sidecar containers must be added to the annotations.

Evict pod with the sidecars and check out annotation.

KEP: [link]
```

---

## B37

```
E2E Proposal: Verify tcpSocket property of v1.Probe along with success and failure threshold.

A E2E to verify `core.v1.tcpSocketAction` resource along with probe's important properties like `successThreshold`, `failureThreshold`, and `periodSeconds`.

Note: following default values are in effect `delay=0s timeout=1s period=10s #success=1 #failure=3`
To improve API coverage based on [label] and their important properties.
[link]

E2E behavior could be:
Create a pod with a container having `tcpSocket` based readiness and liveness probes provided with successThreshold, failureThreshold and periodSeconds values and container should not accept any connection after ~30 sec of it's start. Container MUST be ready after `successThreshold * periodSeconds` (<~30s) is reached. Container MUST NOT be in ready state after `failureThreshold * periodSeconds` (>~30s) is reached.

Note: May need to implement connection closing mechanisam at certain time for `gcr.io/kubernetes-e2e-test-images/liveness:1.1` image to test failureThreshold for `tcp` requests.

[team]
```

---

## B38

```
A completed status pod which request 1 nvidia.com/gpu resource updated to UnexpectedAdmissionError when restart kubelet service

I have a k8s cluster (version v1.23.6) with a GPU node which has 4 GPUs.

Firstly, I submitted a job which request 1 nvidia.com/gpu, and after a while the job successfully finished with a Completed pod status.

Secondly, I submitted a deployment which request 4 nvidia.com/gpu, it keeps ruuning on the GPU node.

Thirdly, I restart the kubelet service on the GPU node, then the job pod updated pod status from Completed to UnexpectedAddmissionError.

Describing the job pod:

The job has completed successfully and release the gpu resource, kubelet should not try to reallocate a GPU resource to a Completed status pod when the kubelet service is restarted.

I expect that the job pod should keep Completed status when kubelet service is restarted.

(1) submitted a job which request 1 nvidia.com/gpu resource, waiting for the job completed,pod status is Completed.
(2) submtted a deployment which request all nvidia.com/gpu resource.
(3) restart kubelet service on the gpu node, and you can see that the job pod updated pod status to UnexpectedAdmissionError.
```

---

## B39

```
aftert re-allocating DeviceManager panic on Allocate()

Based on the following stack trace ,The issue is potentially caused by one goroutine re-allocate device plugin and delete devicesToReuse map [m.devicesToReuse map deleted]
[link]
At the same time, another process is allocating resources ,when creating Pods concurrently
[link]
Another goroutine is allocating device plugin . The devicesToReuse map will be later used in removeContainerAllocatedResources()
[link]
which caused panic. func by itself is not thread-safe

Stack trace:
`Nov 19 15:07:43 cce-xa47m89h-5u0nh5pr-1 kubelet: I1119 15:07:43.942671 11035 manager.go:956] needs re-allocate device plugin resources for pod dag-process-debug-1858716533183492096-202303328_dag-process(4604c558-bfdd-427c-81c9-f1d8a5aea6e7), container main
Nov 19 15:07:43 cce-xa47m89h-5u0nh5pr-1 dockerd: time="2024-11-19T15:07:43.952908939+08:00" level=debug msg="Calling GET /v1.40/images/10.73.150.98:5000/ai-train/onenode:A100_v8/json"
Nov 19 15:07:43 cce-xa47m89h-5u0nh5pr-1 dockerd: time="2024-11-19T15:07:43.954568826+08:00" level=debug msg="Downloaded c4221d178521 to tempfile /data1/cce/docker/tmp/GetImageBlob288125387"
Nov 19 15:07:43 cce-xa47m89h-5u0nh5pr-1 dockerd: time="2024-11-19T15:07:43.955529075+08:00" level=debug msg="Calling POST /v1.40/containers/create?name=k8s_main_dag-process-debug-1858716533183492096-202303328_dag-process_4604c558-bfdd-427c-81c9-f1d8a5aea6e7_0"
Nov 19 15:07:43 cce-xa47m89h-5u0nh5pr-1 dockerd: time="2024-11-19T15:07:43.997696667+08:00" level=debug msg="container mounted via layerStore: &{/data1/cce/docker/overlay2/cf3eea52e7a535afb239d7826d046805c1dfda4fa18eedb3c553ea181d6f7ae5/merged 0x45cc320 0x45cc320}" container=47fdc4b3d17b1d03fcbe58afe8c229ab5132d6d4da237cc9961757a11358cfe6
Nov 19 15:07:43 cce-xa47m89h-5u0nh5pr-1 kubelet: panic: assignment to entry in nil map
Nov 19 15:07:43 cce-xa47m89h-5u0nh5pr-1 kubelet: goroutine 173 [running]:
Nov 19 15:07:43 cce-xa47m89h-5u0nh5pr-1 kubelet: k8s.io/kubernetes/p
```

---

## B40

```
Add events for Volumes

I think it would be beneficial for debugging to add events about volumes in the system. A couple examples:
1. A PV should have an event recorded when it is attached / detached from a node.
2. We should make an event when a mount happens (whether it failed or not)
3. We should make an event when a volume is formatted (whether the format fails or not)

If a volume that requires a cloud provider attach is used directly in a pod, I suggest that event should be generated for that pod where applicable. For example, detach may not be applicable since the pod will necessarily have been deleted or died.

For the record, I think this is probably more applicable to network storage than to things like secrets or configmaps, but it's not strictly PVs, since pods can use volumes directly without using PVs.

[team]
```

---
