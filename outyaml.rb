#!/usr/bin/env ruby

require 'yaml'

require 'rubygems'
require 'bundler/setup'

require 'haml'

$columns = {}
$rows = {}

Haml::Options.defaults[:format] = :html5

class Object
  def try(method, *args, &block)
    send(method, *args, &block) if respond_to?(method)
  end
end

class String
  def strip_heredoc()
    indent = scan(/^[ \t]*(?=\S)/).min.try(:size) || 0
    gsub(/^[ \t]{#{indent}}/, '')
  end
end

def haml(template, **locals)
  engine = Haml::Engine.new(template)
  return engine.render(Object.new(), locals)
end

def render_outline(outline, level=1)
  outline.each do |item|
    item.each do |title, attributes|
      template = <<-TEMPLATE.strip_heredoc
        %h1= title
        %section
          %ul
            - attributes.each do |name, value|
              %li
                = name
                = value
      TEMPLATE
      puts(haml(template, title: title, attributes: attributes))
    end
  end
end

def is_settings?(data)
  if data.is_a?(Hash)
    return (data.has_key?("columns") or data.has_key?("columns"))
  else
    return false
  end
end

def parse_settings(data)
  data.each do |outline|
    if is_settings?(outline)
      $columns = outline.fetch("columns", {})
      $rows = outline.fetch("rows", {})
    end
  end
end

if __FILE__ == $0
  data = YAML.load_stream(STDIN.read())
  parse_settings(data)
  data.each do |outline|
    if not is_settings?(outline)
      render_outline(outline)
    end
  end
  puts(YAML.dump(data))
end
