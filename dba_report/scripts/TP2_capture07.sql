set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl
accept SYSPWD hide prompt 'SYS password: '

conn sys/&SYSPWD@pdborcl as sysdba
alter pluggable database close immediate;
alter pluggable database open read write;
select name, open_mode from v$pdbs;
conn hr/hr@pdborcl
INSERT INTO regions VALUES (5, 'Mars');
commit;
select * from regions;
