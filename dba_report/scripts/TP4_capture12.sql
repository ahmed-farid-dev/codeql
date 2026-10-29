set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

alter session set container = CDB$ROOT;
create undo tablespace undotbs03 datafile '&DIR\undotbs03.dbf' size 20m;
show parameter undo_tablespace
alter system set undo_tablespace = undotbs03 scope = both;
show parameter undo_tablespace
select tablespace_name, contents, status from dba_tablespaces where contents = 'UNDO';
