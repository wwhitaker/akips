
sub web_manual_grouping
{
  # Usage: curl -s "https://{akips-server}/api-script?password={api-rw-pwd};function=web_manual_grouping;type=device;group=maintenance_mode;device={device_name};mode={assign|clear}"

  my $type   = cgi_param ('type')   || "";
  my $group  = cgi_param ('group')  || "";
  my $mode   = cgi_param ('mode')   || "";
  my $device = cgi_param ('device') || "";
  my $child  = cgi_param ('child')  || "";
  my $entity;

  if ($type eq "") {
     errlog ($ERR_DEBUG, "type is missing");
     return;
  }
  elsif ($group eq "") {
     errlog ($ERR_DEBUG, "group is missing");
     return;
  }
  elsif ($mode eq "") {
     errlog ($ERR_DEBUG, "mode is missing");
     return;
  }

  if ($mode eq "assign" || $mode eq "clear") {
     if ($device ne "" && $child ne "") {
        $entity = $device." ".$child;
     }
     else {
        if ($device ne "") {
           $entity = $device;
        }
        else {
           errlog ($ERR_DEBUG, "device is missing");
           return;
        }
     }
  }

  group_manual_load_cfg ();

  given ($mode) {
     when ("add") {
        group_manual_add ($type, $group);
     }

     when ("assign") {
        group_manual_assign ($type, $entity, $group);
     }

     when ("clear") {
        group_manual_clear ($type, $entity, $group);
     }

     when ("delete") {
        group_manual_delete ($type, $group);
     }
  }

  group_manual_save_cfg ();
  adb_flush ();
}

sub web_find_device_by_ip
{
   # Usage: curl -s "https://{akips-server}/api-script?password={api-rw-pwd};function=web_find_device_by_ip;ipaddr={ip-address}"
   
   our $IP2NAME_CFG  = "${HOME_ETC}/ip2name.cfg";
   my $ipaddr        = cgi_param ('ipaddr')    || "";
   my $found_device = 0;
   
   my $IN;
   my $line;
   my %dev;

   if ($ipaddr eq "") {
      errlog ($ERR_DEBUG, "web_find_device_by_ip site-script IP missing");
      printf "IP address is missing\n";
      return;
   }
   
   open ($IN, "<", $IP2NAME_CFG) or EXIT_FATAL ("Could not open $IP2NAME_CFG: $!");

   while ($line = <$IN>) {
      chomp $line;
      %dev = ();
      ($dev{devipaddr}, $dev{device}, $dev{ttime}) = split (",", $line);

      if ($dev{devipaddr} eq $ipaddr) {
         printf "IP Address %s is configured on %s\n", $ipaddr, $dev{device};
         $found_device = 1;
       }
   }
   close $IN;
   
   if ($found_device == 0) {
      printf "IP Address %s is not configured on any devices\n", $ipaddr;
   }
   
   adb_flush ();
}