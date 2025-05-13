#!/bin/bash
# Prebuild hook: remove Elastic Beanstalk default Nginx configs before any provisioning
rm -rf /etc/nginx/conf.d/*
rm -rf /etc/nginx/conf.d/elasticbeanstalk
exit 0