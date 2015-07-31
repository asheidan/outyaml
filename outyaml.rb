#!/usr/bin/env ruby

require 'yaml'

require 'rubygems'
require 'bundler/setup'


if __FILE__ == $0
  data = YAML.load_stream(STDIN.read())
  puts(YAML.dump(data))
end
