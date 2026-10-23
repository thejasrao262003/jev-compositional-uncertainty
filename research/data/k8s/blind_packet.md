# Kubernetes blinded leakage read, third read, after Amendment 6 (40 cleaned issues, new seed)

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
CVE-2017-1002101 - subpath volume mount handling allows arbitrary file access in host filesystem

[CVSS:3.0/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H]([link]

This vulnerability allows containers using [subpath volume mounts]([link] with any volume type (including non-privileged pods, subject to file permissions) to access files/directories outside of the volume, including the host’s filesystem.

Thanks to Maxim Ivanov for reporting this problem.

**Vulnerable versions:**
* Kubernetes 1.3.x-1.6.x
* Kubernetes 1.7.0-1.7.13
* Kubernetes 1.8.0-1.8.8
* Kubernetes 1.9.0-1.9.3

**Vulnerable configurations:**
* Clusters that allow untrusted users to control pod spec content, and prevent host filesystem access via hostPath volumes (or other volume types) using PodSecurityPolicy (or custom admission plugins)
* Clusters that make use of [subpath volume mounts]([link] with untrusted containers or containers that can be compromised

**Vulnerability impact:**
A specially crafted pod spec combined with malicious container behavior can allow read/write access to arbitrary files outside volumes specified in the pod, including the host’s filesystem. This can be accomplished with any volume type, including emptyDir, and can be accomplished with a non-privileged pod (subject to file permissions).

**Mitigations prior to upgrading:**
Prevent untrusted users from creating pods (and pod-creating objects like deployments, replicasets, etc), or [disable all volume types]([link] with PodSecurityPolicy (note that this prevents use of service account tokens in pods, and requires use of [`automountServiceAccountToken: false`]([link]

**Fixed versions:**
* Fixed in v1.7.14 by #61047
* Fixed in v1.8.9 by #61046
* Fixed in v1.9.4 by #61045
* Fixed in master by #61044 (included in v1.10.0-beta.3, will be in v1.10.0)
```

---

## B02

```
Support for 1:N mapping between hostPort and containerPort in Deployment Spec

Currently when we specify a deployment spec with hostNetwork is true and the application in a container listens to multiple ports, the hostPort should be assigned for each of those port.

ports:
- containerPort: 8090
hostPort: 8090
- containerPort: 8091
hostPort : 8091

It would be nice to have range of containerPort for a given hostPort. Something like this below:
ports:
- hostPort: 8090
containerPort: 8090-8200

To add, we are not using the service resource here because these are security applications where it should need host network namespace and avoid SNAT/DNATing. Currently `externalTrafficPolicy: Local` provides such functionality but when run in `hostNetwork: true` it does not matter as the application is directly accessible via pods.
```

---

## B03

```
Add DNS test suite for Conformance E2E

This test suite provide a baseline for commonality between various DNS implementations as mentioned in the [specification document ]([link]
holds various E2E testing DNS functionality and they should adhere to provided specification.

Issue is sourced from [link]

Tracking into umbrella Issue: #73425
```

---

## B04

```
Exclusive CPUs not removed from deleted Pod and put back in the defaultCPUSet.

The `CPUManager` has logic to periodically cleanup stale state and reclaim exclusive CPUs from pods that have recently terminated. It does this by querying the system for a list of `activePods()` and reclaiming CPUs from any pods it is tracking that are not in this list.

This works fine for most pods, but special care needs to be taken to ensure that CPUs are not accidentally reclaimed from pods that have not started yet. Allocation of CPUs to the containers of a pod happens during pod admission (i.e. before the pod is added to the `activePods()` list), so a simple state variable (`pendingAdmissionPod`) is used to indicate which pod is currently being admitted and exclude it from cleanup. Since pod admission is serialized, only one pod will ever be pending admission at a given time, and only a single variable is necessary to track this (i.e. whenever a new pod enters the admission loop to have exclusive CPUs granted to it, `pendingAdmissionPod` is overwritten to point to the new pod, clearing way for the previous one to have its state cleaned up when appropriate).

Unfortunately, this simple procedure can cause problems because `pendingAdmissionPod` is never reset to `nil` after the **last** pod is admitted. This is usually fine, because the next time a pod comes in for admission, it will be overwritten to point to the new pod. But if no new pods come in, then it continues to point to the last pod that we attempted to admit (forever essentially), making it so that we can never cleanup its state if it gets deleted at some point in the future (because it is always treated as an "active" pod so long as it is pointed to by `pendingAdmissionPod`).

I don't think this issue is critical, since in any practical setting pods will be started and stopped all the time, clearing way for the state of previously admitted pods to be cleaned up.
```

---

## B05

```
Kubelet VolumeManager incorrectly marks volume as not "in use" (i.e. safe to detach) while a mount or format is pending

While debugging an issue with a volume getting detached prematurely, @user discovered an issue: the Kubelet VolumeManager incorrectly marks volume as not "in use" (i.e. safe to detach) while a mount or format is pending.

For context, attach/detach controller will not proceed with a detach (after pod referencing a volume is deleted) while the volume is still marked as "in use" by kubelet. Kubelet marks a volume as "in use" before it starts mounting or formating the volume.

The problem is:

* If a pod referencing a volume is deleted while a mount (or format) is pending, then kubelet will go ahead and remove that pod from its "desired state of the world" cache (normally this waits for pod's containers to terminate, but in this case the containers never even started because mount is still pending, i.e. format, is still pending).
* Kubelet volume_manager's `GetVolumesInUse()` method ([link] reports the volume as no longer in use because it is not in desired or actual state (it does not check pending operations <-- this is the bug).
* Attach/detach controller sees the pod delete, checks and sees the volume is not marked as "in use" and proceeds with the detach (incorrectly), but a mount (or format) operation may be pending.
Kubelet volume_manager's `GetVolumesInUse()` method ([link] should count volumes that have pending operations (mount or otherwise) as "in use" (even if they are not in actual or desired state).
While mount is pending (because format is taking a long time, for example), delete the pod referencing the attachable volume.
```

---

## B06

```
Kubelet segfaults when Docker is not running

I was running an experiment to verify that Taints are correctly updated when Condition changes from Unreachable to NotReady and found out that Kubelet can't start when the docker is not running.

I did an experiment on CVM and:
- made `/usr/sbin/kubelet-checker.sh` no op
- made `/usr/sbin/docker-checker.sh` no op
- `service kubelet stop`
- `service docker stop`
- wait
- reverted changes to `kubelet-checker`
- `service kubelet start`

The result is following:

Is this expected, or kubelet should normally start and report itself as 'NotReady'?

[team] @user @user
```

---

## B07

```
Zero value Kubelet PSI metrics emitted even if underlying OS doesn't enable it

In Kubernetes 1.34, the KubeletPSI feature gate was set to true. However, when running Kubernetes on an OS that does not have PSI enabled, the PSI metrics are not expected to be generated. Here are the counts of the metrics observed during a test:

I suspect this part of the code:

[link]

and prometheus does this: [link]

cc: @user @user

There should be no PSI metrics when underlying OS never enables it.

Run k8s 1.34 and above and use grafana to monitor PSI metrics

This is a good to have. Doesn't really impact anything as cardinality is also negligible. This zero value confuses the end-user as it gives a visual impression that PSI is enabled when looking at grafana charts.

I can propose a fix on this.
```

---

## B08

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

## B09

```
CSI migration race condition can cause unexpected detach and data loss

After the cluster was updated to enable PD CSI Driver, there was a race condition where AD Controller (kube-controller-manager) started to [populate the desired state of world]([link] BEFORE the PD CSI Driver was up, thus AD Controller gave us the error

Then AD Controller triggered the disk detach because the disk/volume was not populated in the desired state of world.

Unfortunately the disk was in use during this detach and got corrupted.

Since cluster upgrades can cause the controller manager and CSI drivers to start at different times, the AD controller needs to be more conservative when detaching

We have not been able to reproduce this, it came up from a customer.
```

---

## B10

```
[network-policy] add e2e tests for ipBlock

Test Cases:
- [ ] Ingress blocking based on cidr from a given set of pods
- [ ] Test egress blocking based on cidr to a set of pods
- [ ] Consider an using this cidr feature to fix [Set owner references in pods owned by ProwJobs #3409]([link]
```

---

## B11

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

## B12

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

## B13

```
Creating External Loadbalancer should present some "progress status"

Creating an external loadbalancer takes minutes.

At the same time, the user doesn't know waht is happening, and whether it failed, is in progress, or just the user made a typo in the "externalLoadBalancer"

What we could do for example is:
in the "kubectl get services", if there is external Load Balancer configured, in the place of "external IP" show "status of the load balancer creation".
```

---

## B14

```
pod created failed when devices resource request is 0

1 create deployment by yaml below

2 create pod failed, the reason is

node resource info

expect the pod create success, the request resource is 0, and it must not exceed

so it failed by somewhere unreasonable judgment

1 create pod `a` which use hot pluggable device in resource.request, and the resource is 1
2 remove device
3 create pod `b` which use hot pluggable device in resource.request, and the ressource is 0
```

---

## B15

```
Kubelet admission check includes rejected pods in resource accounting, causing subsequent pods to be incorrectly rejected

The kubelet has a race condition in pod admission logic where rejected pods pollute the resource accounting for subsequent pod admissions.

From Openshift CI logs:
- Pod 1 (pod-out-of-cpu) requested 1000000000000000 millicores (intentionally absurd for testing)
- Rejected at 03:12:06.086 with used: 759 millicores
- Pod 2 (resize-test-kngwb) requested 20 millicores
- Rejected at 03:12:06.220 (134ms later) with used: 1000000000000759 millicores
- This is exactly: 1000000000000000 + 759

The rejected Pod 1's CPU request was incorrectly included in the "used" calculation for Pod 2.

From kubelet logs (worker-2):

CI Run: [link]

Failed Test:
[sig-node] Pod InPlace Resize Container [FeatureGate:InPlacePodVerticalScaling] [Beta]

Rejected pods should not affect resource accounting for subsequent pod admission checks

We have observed this intermittently in Openshift CI.
```

---

## B16

```
Scheduling of pods with RWO volumes

Since RWO volumes work only on a single host, wouldn't it be reasonable for the scheduler to schedule pods for a {RC,RS,D,etc.} that uses such a volume on the same node? Otherwise, pods that land on different nodes are essentially blocked. Deployments are the most affected since you can have a Deployment with just one pod and maxSurge=1 (which is actually the default currently) and with a RWO volume, it will block.

[team] [team] [team]
```

---

## B17

```
HTTP2_PING_TIMEOUT_SECONDS+HTTP2_READ_IDLE_TIMEOUT_SECONDS > 40s will cause all node NotReady

The controller-manager node-lifecycle-controller watches node lease and update `nodeHealthMap` probeTimestamp , and it check node probeTimestamp is before `now - node-monitor-grace-period`. The node-monitor-grace-period default value is 40s.

When the client connection lost, the lease watcher cannot receive new event. With the http2 health check, HTTP2_PING_TIMEOUT_SECONDS default is 30s, HTTP2_READ_IDLE_TIMEOUT_SECONDS default is 15s, it will delay 45s to kill http2 connection.

During this period, node-lifecycle-controller will mark all nodes NotReady.

Here are some logs

When the http2 connection lost, the watch should stop as soon as possible. The reflector should relist resource, and node-lifecycle-controller should not mark all node NotReady.

HTTP2_PING_TIMEOUT_SECONDS+HTTP2_READ_IDLE_TIMEOUT_SECONDS should be less than 40s.

1. Find the controller-manager node-lifecycle-controller watch client srcIP:srcPort. Drop all tcp package send into srcIP:srcPort.
2. Wait for more than 40 seconds, all node will be marked NotReady
3. All node will be Ready after some seconds.
```

---

## B18

```
[FG:InPlacePodVerticalScaling] e2e test does not verify resource update in pod status

e2e tests for pod resizing does not verify if resources in a pod status is updated to the same values in a pod spec after resizing is actuated. This is caused because the result of the runtime support check is reversed:

[link]

Resources in pod status are verified.

Run e2e test with enabling InPlacePodVerticalScaling.

I'm not sure if we should fix it immediately. If this issue is fixed, it will take much longer to finish the tests because there are some issues that it takes much time (60-90s) till resources in a pod status is updated after resizing is actuated such as #123940 and #125559. In addition, pod resize e2e tests are being migrated to e2e node tests in PR #124296.
```

---

## B19

```
Device Plugin failure handling in kubelet is racy

As of now Kubelet removes a resource owned by device plugins as soon as it notices that a plugin has failed (plugin socket is removed, or ListWatch fails). This behavior is undesirable because trivial plugin restarts would result in Node Capacity changes which is most likely going to be monitored in production clusters resulting in alerts.

As discussed in [link] we should have kubelet reduce the capacity and allocatable to `0` if a device plugin has failed and then after a timeout remove the resource completely from the Node object.
This timeout ensures that random restarts do not raise alerts for production cluster admins, while continue failure does raise an alert. It also let's us track scenarios where all devices fail while the device plugin stays healthy.
Similarly, during startup, kubelet should wait to known plugins to re-register prior to declaring a plugin to be unavailable.
I'd ideally expect this bug to be fixed as part of beta.

@user @user @user [team] @user
```

---

## B20

```
Kube-proxy goes in non-operational mode after cleanup without reporting when cleanup job is done

After removing auto-cleanup logic for non-current kube-proxy modes, kube-proxy has to be called manual with flag(see, [link] After switching the proxy mode from to , kube-proxy gets called with the flag and goes in a non-operational loop after [link] When a new svc is created it is non-functional until kube-proxy gets restarted without the flag.
Kube-proxy should report when the cleanup job is done and exit in a clean way. Currently it is hanging in an infinite loop.
```

---

## B21

```
Socket operation on non-socket kubelet error

Hello everyone,

I'm trying to make a Raspberry Pi 2 Kubernetes cluster. I've installed etcd, merged the patches (coreos/etcd#2308), cloned kubernetes and started hack/local-up-cluster.sh (with some modifications, e.g. I built my own kubernetes/pause, removed sudo, because of arch linux).

I'm using arch linux arm.
**_Everything start up fine if I start it via plain docker, e. g. my alpine image or resin/rpi-raspbian, but not if I start via kubernetes**_

Some system info:

But, if I run this

it won't start the pod

When I check the events it says:

Is this a known issue with kubelet?
It would be good to get kubernetes up and running :smile:
```

---

## B22

```
[PodLevelResources] In-place pod resize events do not capture pod-level resources

When issuing in-place pod resize requests, you can view the progress of resizes via events:

but the [podResourceSummary object]([link] that gets marshaled for these events doesn't include pod-level resources, meaning that the allocation emitted is incomplete as it does not contain pod-level resources.

There is a TODO for this: [link]
```

---

## B23

```
kubelet_http_requests_duration_seconds metric records incorrect (near-zero) latency values

The `kubelet_http_requests_duration_seconds` histogram metric always records near-zero values (~2 microseconds) regardless of actual request processing time.

Below is a screenshot from a downstream CI run showing the average latency of kubetet's /metrics/cadvisor endpoint:

<img width="1858" height="842" alt="Image" src="[link] />

The metric should record the actual time taken to handle each HTTP request, from when it's received until the response is sent.

1. Make an HTTP request to the kubelet that takes a measurable amount of time (e.g., `/pods/` endpoint)
2. Query the `kubelet_http_requests_duration_seconds` metric
3. Observe that the recorded duration is always ~2 microseconds instead of the actual processing time

**Root cause:**

In `pkg/kubelet/server/server.go`, the defer statement evaluates `SinceInSeconds(startTime)` immediately when the defer is declared, not when it executes:

In Go, arguments to deferred function calls are evaluated immediately at the defer statement. This means `SinceInSeconds(startTime)` computes the duration at the start of the request (~5µs after `startTime` was set), rather than at the end when the defer actually runs.

This affects observability and SLO tracking for kubelet HTTP endpoints since duration data is meaningless.
```

---

## B24

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

## B25

```
Kubelet UID-qualified exec/run routes ignore mismatched pod UID during pod resolution

While investigating kubelet streaming endpoints, I noticed that the UID-qualified `exec` and `run` routes do not appear to enforce the supplied pod UID during pod resolution.

Routes:

parse and forward the UID, but the underlying lookup prefers the pod full name whenever it is available.

As a result, a request using a stale or mismatched UID can still resolve successfully to the currently running pod with the same namespace/name.

I initially treated this as a potential security concern and performed a deeper investigation of the authorization path.

After tracing the complete request flow multiple times, I could not identify any authorization bypass or privilege escalation. Authorization is already enforced before these handlers, so the observed behavior appears to be a correctness/consistency issue rather than a security issue.

I have reproduced and re-verified this behavior twice using the existing runtime tests and local code tracing.

When a UID-qualified kubelet route is used and a non-empty pod UID is supplied, the request should require both:

- pod full name
- pod UID

to match the current pod.

For example:

should be rejected instead of resolving to the recreated pod.

This would also make the behavior consistent with the existing `attach` and `port-forward` implementations, which explicitly reject UID mismatches.

The existing runtime test already documents the lookup precedence.

Run:

The test demonstrates that:

returns the pod identified by its full name even when the supplied UID belongs to a different pod.

Relevant request flow:

I reproduced this behavior twice during investigation and obtained the same result both times.

Additional investigation:

- Traced the complete kubelet exec/run request path.
- Compared behavior with `attach` and `port-forward`.
- Verified that authorization occurs before the streaming handlers.
```

---

## B26

```
[FG:InPlacePodVerticalScaling] Remove ResizePolicy defaulting

Prior to Kubernetes v1.31, any defaulted change to the pod API could trigger running pods to restart on apiserver upgrade (fixed by [link] Since v1.30 is still within the valid version we cannot set a default ResizePolicy.

Kubelet already handles an unset ResizePolicy as an implicit default (`NotRequired`), so all that is needed here is to remove the defaulting logic. This is probably the preferred behavior even without the version skew issue.
```

---

## B27

```
[SidecarContainers] Failed to get proper phase after the node reboot

If a pod has an init container with restartPolicy "Always" (sidecar), it may lose the pending phase after the node reboot and start the regular containers before initializing the init containers.

This is similar to [link] but separated as it only affects the pod with restartable init containers.

After the node reboot, the remaining pod should start from the pending phase and run the init containers one by one to initialize.

1. Create and initialize the pod with an init container with "Always" container restart policy.
2. Restart the node.
```

---

## B28

```
Pod startup latency regression

In 5k node cluster tests pod startup latency has roughly doubled at all (50th, 90th, 99th, 100th) percentiles, apparently due to some change merged between Oct 16th and 20th. The following graph (for the ci-kubernetes-e2e-gce-scale-performance job) makes it obvious (note values are capped at 10s for readability):

![0jjh2pnsh7p]([link]

The last run with good latency (3.2s@99%) was 49, on October 16th.
Since then it's been between 4.7s and ~5s at 99th %ile.
The [56th run]([link] actually failed because the latency exceeded the threshold (5s). Since we're so close to the threshold, the test is now more flaky.
```

---

## B29

```
[FG:InPlacePodVerticalScaling] api server "INTERNAL_ERROR; received from peer" while executing kubectl replace

error on kubectl replace cmd : error: error when replacing "pod-updated-example.yaml": Put "[link] stream error: stream ID 5; INTERNAL_ERROR; received from peer

On api server logs :

api server return this error : The Pod "XXX" is invalid: spec.containers: Forbidden: pod updates may not add or remove containers

1-start the cluster with FEATURE_GATE ENABLED (InPlacePodVerticalScaling)
2- create a pod with one container , for example :

3- try to replace (without force) with ( + container) :

kubectl replace -f pod-updated-example.yaml

**ERROR** : Put "[link] stream error: stream ID 5; INTERNAL_ERROR; received from peer

based on the master branch (ref commit : 139cc3c659dd1624f7a4bbcc3b07fda79539677a )
```

---

## B30

```
Inconsistent Running/Pending status while pod continues to function

My pods appear to change, randomly but repeatedly, from "Running" to "Pending" status and back, according to "kubectl describe pods". The restart count remains at zero, and I can't find any corresponding errors in any of the kubernetes or docker logs. The pod names (mything-1jq7j, mything-rdd7e) are stable. The restart count remains zero. And during the seeming "pending" periods, I can still _use_ my project -- that is, the "mything" image within the kubernetes pods continues to actively process MQ requests, I don't see any downtime.

Additionally -- I happened to open a second terminal ssh'ed into the same host (which is my kube master host) and watched the describe output in both terminals using:

... which showed me that the "Pending" status would only appear in one terminal window at a time, for 10-20 seconds, during which time the other terminal window (still updating every 1 second) would continue to show the same pod as "Running". Pursuing this further, I made a batch script to run "describe pods" in a background process 1000 times rapid-fire -- within a span of several seconds, I indeed saw the status for one of the pods cycle from "Running" to "Pending" and back. (When I sort the results by order of execution, all of the "Pending" results are together -- that is, only one cycle, not 500 flickers.)

Additionally, when my second pod cycles to "Pending" status like this, the first pod also changes ever so slightly -- specifically the "Node:" output of "describe pods" changes from "10.0.0.4/10.0.0.4" to simply "/10.0.0.4".

**== Output when both pods are "Running" ==**

**== Output when one pod is back to "Pending" ==**

It almost seems like the inconsistency is somewhere in the pod status detection, rather than any actual instability in the pods.
```

---

## B31

```
Add --write-config-to option to kubelet

Add a new `--write-config-to` flag to kubelet, similar to [kube-scheduler]([link] and [kube-proxy]([link]

This flag can be used to render the kubelet configuration file from a set of command-line arguments. For example:

In existing Kubernetes clusters we get lots of warnings like:

But there is no easy way to generate a config file for existing clusters.
```

---

## B32

```
PVCs using `standard` StorageClass create PDs in disks in wrong zone in multi-zone GKE clusters

- Created single-zone cluster in `us-central1-c`
- Expanded to multiple zones after creation using `gcloud container clusters update ... --additional-zones` to `b` and `a`
- Deployed PVC with `storageClassName: standard`, which is a StorageClass included with GKE.
- PV is created in `us-central1-f`, a zone with no nodes from this cluster in it
- PV created in one of the zones that the cluster has nodes in
See `What Happened`. I'm not sure the expansion after creation step is necessary.
May be a duplicate of [link] but that's on AWS
```

---

## B33

```
GCE CreateVolume allocates in chunks of GiB incorrectly

GCE PDs are allocated in chunks of GBs (not GiB) but `CreateVolume` function incorrectly creates volume in chunks of GiB - [link]

cc @user

[team]
```

---

## B34

```
Clean up e2e pods in parallel

There are a couple tests that delete pods in serial, for example:

- [link]
- [link]

We should add a `DeletePodsWithWait` function that cleans up multiple pods in parallel. This can be done by simply deleting each pod before waiting (the waits can be done in serial).
```

---

## B35

```
No share ID in DRA kubelet plugin's API

kubelet plugin API does not support ShareID information. The ShareID is an additional identifier to the device name which may be generated by DRAConsumableCapacity feature ( that is introduced in [link]

The DRA driver which refers to this API for preparing resource needs to pass ShareID to CDI spec's device ID. Otherwise, the same node will fail to create a container according to the duplicate ID.

Pods can be successfully created when sharing the same device with DRAConsumableCapacity.

Enable DRAConsumableCapacity feature, Enable DRA driver with allowMultipleAllocations device, Create two pods allocating the same device.

Without the change to k/k, a driver can have a workaround which wrap the plugin API appending with shareID and use it as a PreparedDevice.

From

to

implemented code: [link]

However, it looks cleaner when we do that in the provided API.
The change needs at driver is only extending the CDI id with share id if not nil: [link]

PR:
- [link]
```

---

## B36

```
Expose container's own identity to the container

Container can be identified in the cluster at a given point of time by a tuple `(namespace, pod_name, container_name)`. Currently, the only guaranteed way to get this information is Downward API, which requires quite lengthy definition in the container's spec.

However, this information is extremely important for monitoing/logging client libraries. They would benefit from being able to out of the box send the information to the backend without querying Kubernetes API or a separate agent. Example issue: [link]

[team]
```

---

## B37

```
Restarting kubelet with new node labels doesn't update labels for node

kubelet version: 1.2.4

Steps to reproduce:
- start kubelet with some labels using the `--node-labels` flag
- wait for the node to register itself with the master
- restart kubelet with a different set of labels

Expected result:
`kubectl get no --show-labels` shows the node with the updated labels

Actual result:
`kubectl get no --show-labels` shows the node with the original labels
```

---

## B38

```
DRA: kubelet: checkpoint checksum changes when API gets extended

When adding the `StructuredData` field to `resourcev1alpha2.ResourceHandle`, old checkpoint files became invalid because the checksum that gets calculated by hashing the `spew` output in `pkg/util/hash` no longer matches. This caused kubelet to fail to start with:

Here's what the checksum in a unit test gets calculcated for:

Note the new `StructuredData:(*v1alpha2.StructuredResourceHandle)<nil>`.

Not sure what the right behavior is. Perhaps kubelet should have ignored the invalid checkpoint?

Revert the pkg/kubelet/cm/dra/state/state_checkpoint_test.go update in [link]

The state.DRAManagerCheckpoint contains a version field, which is set to v1.I think that's where things fall apart: that version must exactly match the type that gets serialized, which is not the case here. The type changes over time, but the version is fixed.

Let's reconsider what should get checkpointed and how we can make that stable. Also, is checkpointing really worth it? What bad things happen if we remove it?
```

---

## B39

```
node node summary metrics missing pods on systemd

When running on a systemd host, pod metrics don't show up in the summary api. Can be tested on ubuntu wily.
```

---

## B40

```
Simplify grace period related code in NodeController

The code is hard to understand and debug. Related issue: #14652.

cc: @user @user @user @user @user
```

---
