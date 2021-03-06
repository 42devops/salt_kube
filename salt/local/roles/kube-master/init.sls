include:
  - caserver.ca-cert
  - cert
  - kube-apiserver
  - kube-controller-manager
  - kube-scheduler
  - kube-addons.coredns
  - vault
{% if salt['pillar.get']('cni:plugin', 'flannel').lower() == "cilium" %}
  - kube-cni.cilium.install
{% endif %}
{% if salt['pillar.get']('istio:enable', 'false') %}
  - istio.install
{% endif %}