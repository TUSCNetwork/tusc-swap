create table transfers(
    id                      SERIAL,
    eth_transaction_hash    varchar(255) unique not null,
    tusc_account_name       varchar(255) not null,
    occ_amount              bigint not null,
    tusc_amount             bigint not null,
    created_at              timestamp without time zone default (now() at time zone 'utc'),
    primary key (id, eth_transaction_hash)
);

create table highest_blocks_handled(
    id                SERIAL,
    block_number      integer not null,
    created_at        timestamp without time zone default (now() at time zone 'utc'),
    primary key (id)
);