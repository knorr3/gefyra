import docker
from docker.models.containers import Container

from gefyra.configuration import ClientConfiguration
from gefyra.local.utils import (
    build_cargo_image,
    handle_docker_create_container,
    handle_docker_remove_container,
)


def create_cargo_container(
    config: ClientConfiguration, cargo_connection_data: dict
) -> Container:
    wireguard_ip = f"{cargo_connection_data['Interface.Address']}"
    private_key = cargo_connection_data["Interface.PrivateKey"]
    dns = (
        f"{cargo_connection_data['Interface.DNS']} {config.NAMESPACE}.svc.cluster.local"
    )
    public_key = cargo_connection_data["Peer.PublicKey"]
    # docker to work with ipv4 only
    allowed_ips = cargo_connection_data["Peer.AllowedIPs"].split(",")[0]

    # build image
    image, build_logs = build_cargo_image(
        config,
        wireguard_ip=wireguard_ip,
        private_key=private_key,
        dns=dns,
        public_key=public_key,
        endpoint=config.CARGO_ENDPOINT,
        allowed_ips=allowed_ips,
    )
    # we only have one tag
    image_name_and_tag = image.tags[0]
    # run image
    container = handle_docker_create_container(
        config,
        image_name_and_tag,
        detach=True,
        name=config.CARGO_CONTAINER_NAME,
        auto_remove=True,
        cap_add=["NET_ADMIN"],
        privileged=True,
    )
    return container


def remove_cargo_container(config: ClientConfiguration):
    try:
        handle_docker_remove_container(config, container_id=config.CARGO_CONTAINER_NAME)
    except docker.errors.NotFound:
        pass


def get_cargo_ip_from_netaddress(network_address: str) -> str:
    return ".".join(network_address.split(".")[:3]) + ".149"