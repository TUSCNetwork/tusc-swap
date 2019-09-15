create table mainnet_recovery(
    id                      SERIAL,
    eth_transaction_hash    text unique not null,
    tusc_account_name       text not null,
    occ_amount              text not null,
    tusc_amount             text not null,
    tusc_public_key         TEXT NOT NULL DEFAULT '',
    swap_performed          bool default false,
    created_at              timestamp without time zone default (now() at time zone 'utc'),
    primary key (id, eth_transaction_hash)
);

insert into mainnet_recovery (eth_transaction_hash, tusc_account_name, occ_amount, tusc_amount)
select eth_transaction_hash, tusc_account_name, occ_amount, tusc_amount from transfers;

-- Account registration tracking
create table tusc_account_registrations(
    id                      SERIAL,
    tusc_account_name       text not null,
    tusc_public_key         TEXT NOT NULL DEFAULT '',
    created_at              timestamp without time zone default (now() at time zone 'utc'),
    primary key (id, tusc_account_name)
);

insert into tusc_account_registrations (tusc_account_name, tusc_public_key)
select distinct tusc_account_name, tusc_public_key from mainnet_recovery order by tusc_account_name asc;

-- Manually set highest block number