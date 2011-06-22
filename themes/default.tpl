<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>{{ site.settings.TITLE }}</title>
    <base href="{{ base }}" />
    <link rel="stylesheet" href="static/css/style.css" />
    <link rel="alternate" type="application/rss+xml" title="RSS" href="rss.xml" />
    <script src="static/js/jquery.js"></script>
    <script src="static/js/jquery.infinitescroll.min.js"></script>
    <script>
      $(document).ready(function() {
      $('#posts').infinitescroll({
      navSelector  : ".nav",     
      nextSelector : "div.nav a.older",    
      itemSelector : "#posts" }
      );});
    </script>
   {% block header %}{% endblock %}
  </head>
  
  <body>
   <div id="header">

     <h1><a href=".">{{ site.settings.TITLE }}</a></h1>    
     {% if site.settings.DESCRIPTION %}
     <div class="description">
       {{ site.settings.DESCRIPTION }}
     </div>
     {% endif %}

     {% if directory %}
     <h2><a href="{{ directory }}">{{ directory }}</a></h2>
     {% endif %}

   </div>

    <div id="content">
      {% if site.directories %}
      <div id="directories">
	<a href=".">home</a><br /><br />
	{% for d in site.directories %}
	<a href="{{ d }}/"
	{% if d == directory %}style="font-weight: bold;"{% endif %}
	>{{ d }}</a><br />
	{% endfor %}
      </div>
      {% endif %}
      
      {% block posts %}
      <div id="posts">	
	{% for post in posts %}
	<div class="post {{ post.type }}">
	  {% if post.type == 'audio' %}
	  <p>
	    <audio src="{{ post.url }}" controls autobuffer></audio>
	  </p>
	  <p>
	    {{ post.audio_title }} &middot; {{ post.audio_artist }} &middot; {{ post.audio_album }}
	  </p>
	  {% endif %}
	  
	  {% if post.type == 'default' %}
	  <h2><a href="{{ post.url }}">{{ post.filename }}</a></h2>
	  {% endif %}

	  {% if post.type == 'image' %}
	  <div class="bigimg">
	    <a href="{{ post.url }}"><img src="{{ post.url }}" alt="{{ post.filename }}" title="{{ post.filename }}"/></a>
	  </div>
	  {% endif %}

	  {% if post.type == 'text' %}
	  {{ post.markdown_text }}
	  {% endif %}

	  {% if post.type == 'video' %}
	  <p>
	    <video src="{{ post.url }}" controls></video>
	  </p>
	  {% endif %}

	  {% if post.type == 'webloc' %}
	  <h2><a href="{{ post.target_url }}">{{ post.target_url }}</a></h2>
	  {% endif %}

	  {% if post.finder_comment %}
	  <p class="commentary">{{ post.finder_comment }}</p>
	  {% endif %}
	  <p class="timestamp">
	    <a href="{{ post.permafile }}">{{ post.prettydate }} {{ post.prettytime }}</a> &middot; <a href="{{ post.url }}">{{ post.filename }}</a>
	    {% if post.source_url %}
	    &middot; <a href="{{ post.source_url }}">via {{ post.source_url }}</a>
	    {% endif %}
	    {% if post.directory %}
	    <br /><b><a href="{{ post.directory }}">{{ post.directory }}</a></b>
	    {% endif %}
	  </p>
	</div>
	{% endfor %}
      </div>
      {% endblock %}
      

      {% if page %}
      <div class="nav">
	{% if page > 1 %}
	<a href="{{ directory }}/{{ page-1 }}.html" class="newer">newer</a>
	{% endif %}
	
      {% if page < last_page %}
		   <a href="{{ directory }}/{{ page+1 }}.html" class="older">older</a>
		   {% endif %}
      </div>
      {% endif %}
    </div>

  </body>
</html>
