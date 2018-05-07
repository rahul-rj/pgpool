Repository for postgresql and pgpool

1) pgpool: Used as a middleware service between postgresql-server and postgresql-client. 
           Required to perform the automatic switchover in case of failure of master DB.
           Also works as a load balancer, reads from both DBs as DBs are in replication
           mode and writes to the Master DB.

2) postgresql: The Master/Slave server with streaming replication enabled.
