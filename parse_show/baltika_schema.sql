create table L2 (
    hostname    text ,
    host_ip    text,
    port    text,
    mac    text,
    ip    text,
    type    text,
    speed    text
);

create table cdp (
    hostname    text,
    local_port    text,
    remote_hostname    text,
    remote_port    text	
);


create table ARP (
    mac    text primary key,
    ip    text,
    vlan    text,
    hostname    text
);
