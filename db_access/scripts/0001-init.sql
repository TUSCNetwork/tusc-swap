create table transfers(
    id                      SERIAL,
    eth_transaction_hash    text unique not null,
    tusc_account_name       text not null,
    occ_amount              text not null,
    tusc_amount             text not null,
    created_at              timestamp without time zone default (now() at time zone 'utc'),
    primary key (id, eth_transaction_hash)
);

create table highest_blocks_handled(
    id                SERIAL,
    block_number      integer not null,
    created_at        timestamp without time zone default (now() at time zone 'utc'),
    primary key (id)
);