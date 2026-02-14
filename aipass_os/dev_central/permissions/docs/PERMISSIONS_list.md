# Permissions List

## List ACL permissions system-wide:

### System

$ sudo find / -exec getfacl --skip-base {} \; 2>/dev/null | head -50

### Active Permissions

$ sudo setfacl -m u:aipass:rwx /
$ sudo setfacl -m u:aipass:rwx /etc/claude-code
$ sudo setfacl -m m::rwx /home



## Common Commands
```
## example:
sudo mv /AIPass_memory_templates /home/
```


