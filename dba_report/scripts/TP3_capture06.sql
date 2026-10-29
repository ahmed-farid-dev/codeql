set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

show parameter db_block_size
select * from v$sga;
show sga
select name, value from v$pgastat where name in ('aggregate PGA target parameter','total PGA allocated','maximum PGA allocated');
select parameter, value from v$option where value = 'TRUE' order by 1;
