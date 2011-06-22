<?xml version="1.0" encoding="UTF-8" ?> 
<rss version="2.0">
<channel>
  <title>{{ site.settings.TITLE }}</title>
  <link>{{ site.settings.URL }}</link> 
  <description>{{ site.settings.DESCRIPTION }}</description>
  {% for post in posts[:15]: %}
  <item>
    
    <link>{{ site.settings.URL }}{{ post.permafile }}</link>
    <description><![CDATA[ 

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
	  <p>
	    <a href="{{ post.url }}"><img src="{{ post.medium }}" alt="{{ post.filename }}" title="{{ post.filename }}"/></a>
	  </p>
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

 ]]></description>
  </item>
  {% endfor %}
</channel>
</rss>