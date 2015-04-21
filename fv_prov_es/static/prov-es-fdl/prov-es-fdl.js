// set canvas attributes
var width = $('#chart').innerWidth(),
    height = window.innerHeight - 
             parseInt($('body').css('padding-top').replace("px", "")) + 
             parseInt($('body').css('padding-bottom').replace("px", "")),
    radiusLength = 15,
    polyLength = 10,
    rectLength = 18,
    markerLength = 6;

// declare globals
var addVizUrl = null;
var force = null;
var svg = null;
var defs = null;
var nodes = [];
var nodesDict = {};
var links = [];
var linksDict = {};
var tip = null;
var allGroup = null;
var pathGroup = null;
var agentGroup = null;
var nodeTextGroup = null;
var pathTextGroup = null;
var entsGroup = null;
var actsGroup = null;
var forceEnabled = false;
var clickedOnce = false;
var timer;

// concepts to hide label for
var hideLabel = {
  entity: true,
  activity: true,
  agent: true,
  path: true
};

// show human readable name
var showHumanReadable = true;


// return random integer between 2 numbers
function rand_int(min, max) {
  return Math.floor(Math.random()*(max-min+1)+min);
}


// handler to set CSS class to show text shadow
function show(d, i) {
  if (i % 2 == 0) return "shadow";
  else return null;
}


// handler to set CSS class to hide text
function hide(d, i) {
  return "hidden";
}


// function that returns the svg text nodes that match current node
function getMatchedTextNodes(d) {
  // get text nodes for this entity
  return nodeTextGroup.selectAll("g text")
    .filter(function(e) {
      // match text node to the shape node that is currently selected
      if ((d.id == e.id) && d3.select(this).attr("node_idx") == d.index) return true;
      return false;
    });
}


// handler to show text on the current node
function showText(d) {
  getMatchedTextNodes(d).attr("class", show);
}


// handler to hide text on the current node
function hideText(d) {
  getMatchedTextNodes(d).attr("class", hide);
}


// function that returns the svg text nodes that match current path
function getMatchedPathTextNodes(d) {
  // get text nodes for this path
  return pathTextGroup.selectAll("g text")
    .filter(function(e) {
      // match text node to the path that is currently selected
      if (d.id == e.id) return true;
      return false;
    });
}


// handler to show text on the current node
function showPathText(d) {
  getMatchedPathTextNodes(d).attr("class", show);
}


// handler to hide text on the current node
function hidePathText(d) {
  getMatchedPathTextNodes(d).attr("class", hide);
}


// handler to hide or show tip
function toggleTip(d, e) {
  if (parseInt(tip.style('opacity')) == 0) tip.show(d);
    else tip.hide(d);
  }


// handler to show info window of an node
function showInfo(d) {
  return "translate(480,480)scale(46)rotate(180)";
  //return "translate(" + ((document.body.clientWidth-460/2)-230) + ",480)scale(46)rotate(180)"; 
}


function jq( myid ) {
  return "#" + myid.replace( /(:|\.|\[|\])/g, "\\$1" );
}


function set_left_margin() {
  return ($(window).width() - $(this).width())/2;
}


// resize canvas
function resize() {
  width = $('#chart').innerWidth();
  height = window.innerHeight - 
           parseInt($('body').css('padding-top').replace("px", "")) + 
           parseInt($('body').css('padding-bottom').replace("px", ""));
  svg.attr("width", width).attr("height", height);
  force.size([width, height]).resume();
}


// create link to used
function link_used(src_x, src_y, tgt_x, tgt_y, do_curve) {
  var dx = tgt_x - src_x + rectLength/2,
      dy = tgt_y - src_y + rectLength/2,
      dr = Math.sqrt(dx * dx + dy * dy);
  if (isNaN(dx) || isNaN(dy) || isNaN(dr)) return null;
  // specify source and target of paths taking into account offsets to get to node center
  if (do_curve == true) {
    return "M" + Math.max(rectLength, Math.min(width - rectLength, src_x)) + "," + 
           Math.max(rectLength, Math.min(height - rectLength, src_y)) + "A" + dr + 
           "," + dr + " 0 0,1 " + (Math.max(rectLength, Math.min(width - rectLength, tgt_x)) + rectLength/2) + 
           "," + (Math.max(rectLength, Math.min(height - rectLength, tgt_y)) + rectLength/2);
  }
  return "M" + Math.max(rectLength, Math.min(width - rectLength, src_x)) + "," + 
         Math.max(rectLength, Math.min(height - rectLength, src_y)) + "L" +
         (Math.max(rectLength, Math.min(width - rectLength, tgt_x)) + rectLength/2) + 
         "," + (Math.max(rectLength, Math.min(height - rectLength, tgt_y)) + rectLength/2);
}


// create link to wasGeneratedBy
function link_wasGeneratedBy(src_x, src_y, tgt_x, tgt_y, do_curve) {
  var dx = tgt_x - src_x + rectLength/2,
      dy = tgt_y - src_y + rectLength/2,
      dr = Math.sqrt(dx * dx + dy * dy);
  if (isNaN(dx) || isNaN(dy) || isNaN(dr)) return null;
  // specify source and target of paths taking into account offsets to get to node center
  if (do_curve == true) {
    return "M" + (Math.max(rectLength, Math.min(width - rectLength, src_x)) + rectLength/2) + "," + 
           (Math.max(rectLength, Math.min(height - rectLength, src_y)) + rectLength/2) + "A" + dr + 
           "," + dr + " 0 0,1 " + Math.max(rectLength, Math.min(width - rectLength, tgt_x)) + 
           "," + Math.max(rectLength, Math.min(height - rectLength, tgt_y));
  }
  return "M" + (Math.max(rectLength, Math.min(width - rectLength, src_x)) + rectLength/2) + "," + 
    (Math.max(rectLength, Math.min(height - rectLength, src_y)) + rectLength/2) + "L" +
    Math.max(rectLength, Math.min(width - rectLength, tgt_x)) + 
    "," + Math.max(rectLength, Math.min(height - rectLength, tgt_y));
}


// create association links
function link_association(src_x, src_y, tgt_x, tgt_y) {
  var dx = tgt_x - src_x + rectLength/2,
      dy = tgt_y - src_y + rectLength/2,
      dr = Math.sqrt(dx * dx + dy * dy);
  if (isNaN(dx) || isNaN(dy) || isNaN(dr)) return null;
  // specify source and target of paths taking into account offsets to get to node center
  return "M" + Math.max(rectLength, Math.min(width - rectLength, src_x) + rectLength/2) + "," + 
         Math.max(rectLength, Math.min(height - rectLength, src_y) + rectLength/2) + "A" + dr + 
         "," + dr + " 0 0,1 " + Math.max(rectLength, Math.min(width - rectLength, tgt_x)) + 
         "," + Math.max(rectLength, Math.min(height - rectLength, tgt_y));
}


// create controlled links
function link_controlled(src_x, src_y, tgt_x, tgt_y) {
  var dx = tgt_x - src_x + polyLength/2,
      dy = tgt_y - src_y + polyLength/2,
      dr = Math.sqrt(dx * dx + dy * dy);
  if (isNaN(dx) || isNaN(dy) || isNaN(dr)) return null;
  // specify source and target of paths taking into account offsets to get to node center
  return "M" + (Math.max(rectLength, Math.min(width - rectLength, src_x)) + polyLength) + 
         "," + (Math.max(rectLength, Math.min(height - rectLength, src_y)) + polyLength) + "A" + dr + 
         "," + dr + " 0 0,1 " + Math.max(rectLength, Math.min(width - rectLength, tgt_x)) + 
         "," + Math.max(rectLength, Math.min(height - rectLength, tgt_y));
}


// create entity to entity related link
function link_e2e_related(src_x, src_y, tgt_x, tgt_y, do_curve) {
  var dx = tgt_x - src_x + rectLength/2,
      dy = tgt_y - src_y + rectLength/2,
      dr = Math.sqrt(dx * dx + dy * dy);
  if (isNaN(dx) || isNaN(dy) || isNaN(dr)) return null;
  // specify source and target of paths taking into account offsets to get to node center
  if (do_curve == true) {
    return "M" + Math.max(rectLength, Math.min(width - rectLength, src_x) + rectLength/2) + "," + 
           Math.max(rectLength, Math.min(height - rectLength, src_y) + rectLength/2) + "A" + dr + 
           "," + dr + " 0 0,1 " + (Math.max(rectLength, Math.min(width - rectLength, tgt_x)) +  + rectLength/2) + 
           "," + (Math.max(rectLength, Math.min(height - rectLength, tgt_y)) + rectLength/2);
  }
  return "M" + Math.max(rectLength, Math.min(width - rectLength, src_x) + rectLength/2) + "," + 
         Math.max(rectLength, Math.min(height - rectLength, src_y) + rectLength/2) + "L" +
         (Math.max(rectLength, Math.min(width - rectLength, tgt_x)) + rectLength/2) + 
         "," + (Math.max(rectLength, Math.min(height - rectLength, tgt_y)) + rectLength/2);
}


// create entity to entity related link
function link_a2e_related(src_x, src_y, tgt_x, tgt_y, do_curve) {
  var dx = tgt_x - src_x + rectLength/2,
      dy = tgt_y - src_y + rectLength/2,
      dr = Math.sqrt(dx * dx + dy * dy);
  if (isNaN(dx) || isNaN(dy) || isNaN(dr)) return null;
  // specify source and target of paths taking into account offsets to get to node center
  if (do_curve == true) {
    return "M" + Math.max(rectLength, Math.min(width - rectLength, src_x)) + "," + 
           Math.max(rectLength, Math.min(height - rectLength, src_y)) + "A" + dr + 
           "," + dr + " 0 0,1 " + (Math.max(rectLength, Math.min(width - rectLength, tgt_x)) + rectLength/2) + 
           "," + (Math.max(rectLength, Math.min(height - rectLength, tgt_y)) + rectLength/2);
  }
  return "M" + Math.max(rectLength, Math.min(width - rectLength, src_x)) + "," + 
         Math.max(rectLength, Math.min(height - rectLength, src_y)) + "L" +
         (Math.max(rectLength, Math.min(width - rectLength, tgt_x)) + rectLength/2) + 
         "," + (Math.max(rectLength, Math.min(height - rectLength, tgt_y)) + rectLength/2);
}


// Use elliptical arc path segments to doubly-encode directionality.
function tick() {
  pathGroup.selectAll("path").attr("d", function(d) {
    if (d.type == "wasGeneratedBy") {
      return link_wasGeneratedBy(d.source.x, d.source.y, d.target.x, d.target.y, false);
    }
    if (d.type == "used") {
      return link_used(d.source.x, d.source.y, d.target.x, d.target.y, false);
    }
    if (d.type == "associated") {
      return link_association(d.source.x, d.source.y, d.target.x, d.target.y);
    }
    if (d.type == "controlled") {
      return link_controlled(d.source.x, d.source.y, d.target.x, d.target.y);
    }
    if (d.type == "e2e_related") {
      return link_e2e_related(d.source.x, d.source.y, d.target.x, d.target.y, true);
    }
    if (d.type == "a2e_related") {
      return link_a2e_related(d.source.x, d.source.y, d.target.x, d.target.y, true);
    }
  });

  agentGroup.selectAll("polygon").attr("transform", function(d) {
    var x = Math.max(rectLength, Math.min(width - rectLength, d.x));
    var y = Math.max(rectLength, Math.min(height - rectLength, d.y));
    if (isNaN(x) || isNaN(y)) return null;
    return "translate(" + x + "," + y + ")";
  });

  actsGroup.selectAll("circle").attr("transform", function(d) {
    var x = Math.max(radiusLength, Math.min(width - radiusLength, d.x));
    var y = Math.max(radiusLength, Math.min(height - radiusLength, d.y));
    if (isNaN(x) || isNaN(y)) return null;
    return "translate(" + x + "," + y + ")";
  });

  entsGroup.selectAll("rect").attr("transform", function(d) {
    var x = Math.max(rectLength, Math.min(width - rectLength, d.x));
    var y = Math.max(rectLength, Math.min(height - rectLength, d.y));
    if (isNaN(x) || isNaN(y)) return null;
    return "translate(" + x + "," + y + ")";
  });

  nodeTextGroup.selectAll("g").attr("transform", function(d) {
    var x = Math.max(rectLength, Math.min(width - rectLength, d.x));
    var y = Math.max(rectLength, Math.min(height - rectLength, d.y));
    if (isNaN(x) || isNaN(y)) return null;
    return "translate(" + x + "," + y + ")";
  });

  pathTextGroup.selectAll("g").attr("transform", function(d) {
    //var bbox = $(jq(d.id)).get()[0].getBBox();
    //var x = Math.floor(bbox.x + bbox.width/2.0);
    //var y = Math.floor(bbox.y + bbox.height/2.0); 
    //if (isNaN(x) || isNaN(y)) return null;
    //return "translate(" + x + "," + y + ")";
    if (d.source.x > d.target.x) var x = d.target.x + (d.source.x - d.target.x)/2.;
    else var x = d.source.x + (d.target.x - d.source.x)/2.;
    if (d.source.y > d.target.y) var y = d.target.y + (d.source.y - d.target.y)/2.;
    else var y = d.source.y + (d.target.y - d.source.y)/2.;
    if (isNaN(x) || isNaN(y)) return null;
    return "translate(" + x + "," + y + ")";
  });
}


// set node locations according to graphviz
function setGraphVizLocs() {
  agentGroup.selectAll("polygon").on('mousedown.drag', null).transition().duration(500)
    .attr("transform", function(d) {
      var x = Math.max(rectLength, Math.min(width - rectLength, d.gv_x));
      var y = Math.max(rectLength, Math.min(height - rectLength, d.gv_y));
      if (isNaN(x) || isNaN(y)) return null;
      return "translate(" + x + "," + y + ")";
  });

  actsGroup.selectAll("circle").on('mousedown.drag', null).transition().duration(500)
    .attr("transform", function(d) {
      var x = Math.max(radiusLength, Math.min(width - radiusLength, d.gv_x));
      var y = Math.max(radiusLength, Math.min(height - radiusLength, d.gv_y));
      if (isNaN(x) || isNaN(y)) return null;
      return "translate(" + x + "," + y + ")";
  });

  entsGroup.selectAll("rect").on('mousedown.drag', null).transition().duration(500)
    .attr("transform", function(d) {
      var x = Math.max(rectLength, Math.min(width - rectLength, d.gv_x));
      var y = Math.max(rectLength, Math.min(height - rectLength, d.gv_y));
      if (isNaN(x) || isNaN(y)) return null;
      return "translate(" + x + "," + y + ")";
  });

  nodeTextGroup.selectAll("g").transition().duration(500)
    .attr("transform", function(d) {
      var x = Math.max(rectLength, Math.min(width - rectLength, d.gv_x));
      var y = Math.max(rectLength, Math.min(height - rectLength, d.gv_y));
      if (isNaN(x) || isNaN(y)) return null;
      return "translate(" + x + "," + y + ")";
  });
  
  pathGroup.selectAll("path").transition().duration(500)
    .attr("d", function(d) {
      if (d.type == "wasGeneratedBy") {
        return link_wasGeneratedBy(d.source.gv_x, d.source.gv_y, d.target.gv_x, d.target.gv_y, false);
      }
      if (d.type == "used") {
        return link_used(d.source.gv_x, d.source.gv_y, d.target.gv_x, d.target.gv_y, false);
      }
      if (d.type == "associated") {
        return link_association(d.source.gv_x, d.source.gv_y, d.target.gv_x, d.target.gv_y);
      }
      if (d.type == "controlled") {
        return link_controlled(d.source.gv_x, d.source.gv_y, d.target.gv_x, d.target.gv_y);
      }
      if (d.type == "e2e_related") {
        return link_e2e_related(d.source.gv_x, d.source.gv_y, d.target.gv_x, d.target.gv_y, true);
      }
      if (d.type == "a2e_related") {
        return link_a2e_related(d.source.gv_x, d.source.gv_y, d.target.gv_x, d.target.gv_y, true);
      }
  });

  pathTextGroup.selectAll("g").transition().duration(500)
    .attr("transform", function(d) {
      if (d.source.gv_x > d.target.gv_x) var x = d.target.gv_x + (d.source.gv_x - d.target.gv_x)/2.;
      else var x = d.source.gv_x + (d.target.gv_x - d.source.gv_x)/2.;
      if (d.source.gv_y > d.target.gv_y) var y = d.target.gv_y + (d.source.gv_y - d.target.gv_y)/2.;
      else var y = d.source.gv_y + (d.target.gv_y - d.source.gv_y)/2.;
      if (isNaN(x) || isNaN(y)) return null;
      return "translate(" + x + "," + y + ")";
  });
  
  // center the nodes - this needs to be fixed so that it doesn't shift the canvas
  /*
  var g_bbox = allGroup.node().getBoundingClientRect();
  allGroup.transition().duration(500)
    .attr("transform", function(d) {
      return "translate(" + (width/2 - g_bbox.width/2) + "," + (height/2 - g_bbox.height/2) + ")";
  });
  */

}


// enable force dragging
function enableForce() {
  agentGroup.selectAll("polygon").call(force.drag).transition().duration(500)
    .attr("transform", function(d) {
      var x = Math.max(rectLength, Math.min(width - rectLength, d.x));
      var y = Math.max(rectLength, Math.min(height - rectLength, d.y));
      if (isNaN(x) || isNaN(y)) return null;
      return "translate(" + x + "," + y + ")";
  });

  actsGroup.selectAll("circle").call(force.drag).transition().duration(500)
    .attr("transform", function(d) {
      var x = Math.max(radiusLength, Math.min(width - radiusLength, d.x));
      var y = Math.max(radiusLength, Math.min(height - radiusLength, d.y));
      if (isNaN(x) || isNaN(y)) return null;
      return "translate(" + x + "," + y + ")";
  });

  entsGroup.selectAll("rect").call(force.drag).transition().duration(500)
    .attr("transform", function(d) {
      var x = Math.max(rectLength, Math.min(width - rectLength, d.x));
      var y = Math.max(rectLength, Math.min(height - rectLength, d.y));
      if (isNaN(x) || isNaN(y)) return null;
      return "translate(" + x + "," + y + ")";
  });

  nodeTextGroup.selectAll("g").transition().duration(500)
    .attr("transform", function(d) {
      var x = Math.max(rectLength, Math.min(width - rectLength, d.x));
      var y = Math.max(rectLength, Math.min(height - rectLength, d.y));
      if (isNaN(x) || isNaN(y)) return null;
      return "translate(" + x + "," + y + ")";
  });
  
  pathGroup.selectAll("path").transition().duration(500)
    .attr("d", function(d) {
      if (d.type == "wasGeneratedBy") {
        return link_wasGeneratedBy(d.source.x, d.source.y, d.target.x, d.target.y, false);
      }
      if (d.type == "used") {
        return link_used(d.source.x, d.source.y, d.target.x, d.target.y, false);
      }
      if (d.type == "associated") {
        return link_association(d.source.x, d.source.y, d.target.x, d.target.y);
      }
      if (d.type == "controlled") {
        return link_controlled(d.source.x, d.source.y, d.target.x, d.target.y);
      }
      if (d.type == "e2e_related") {
        return link_e2e_related(d.source.x, d.source.y, d.target.x, d.target.y, true);
      }
      if (d.type == "a2e_related") {
        return link_a2e_related(d.source.x, d.source.y, d.target.x, d.target.y, true);
      }
  });

  pathTextGroup.selectAll("g").transition().duration(500)
    .attr("transform", function(d) {
      if (d.source.x > d.target.x) var x = d.target.x + (d.source.x - d.target.x)/2.;
      else var x = d.source.x + (d.target.x - d.source.x)/2.;
      if (d.source.y > d.target.y) var y = d.target.y + (d.source.y - d.target.y)/2.;
      else var y = d.source.y + (d.target.y - d.source.y)/2.;
      if (isNaN(x) || isNaN(y)) return null;
      return "translate(" + x + "," + y + ")";
  });
}


function addNodesAndLinks(json) {
  json.nodes.forEach(function(n) {
    if (nodesDict[n.id] === undefined) {
      nodes.push(n);
      nodesDict[n.id] = nodes.length - 1;
    }
  });
      
  // adjust source and target indexes
  var new_links = [];
  var newLinksDict = {};
  links.forEach(function(l, i) {
    var src = nodesDict[l.source.id];
    var tgt = nodesDict[l.target.id];
    if (src !== undefined && tgt !== undefined) {
      var link_id = src + '_' + tgt;
      new_links.push({
        id: link_id,
        source:src,
        target:tgt,
        type:l.type,
        value:l.value,
        concept:l.concept,
        doc:l.doc
      });
      newLinksDict[link_id] = true;
    }
  });
  json.links.forEach(function(l) {
    var src = nodesDict[json.nodes[l.source].id];
    var tgt = nodesDict[json.nodes[l.target].id];
    var link_id = src + '_' + tgt;
    if (newLinksDict[link_id] === undefined) {
      new_links.push({
        id: link_id,
        source:src,
        target:tgt,
        type:l.type,
        value:l.value,
        concept:l.concept,
        doc:l.doc
      });
    }
  });
      
  // get graphviz location info
  $.ajax({
    url: addVizUrl + '/layout',
    data: {viz_dict: JSON.stringify({links: new_links, nodes: nodes}, null)},
    type: 'POST',
    success: function(data, sts, xhr) {
      data.nodes.forEach(function(nn, ni) {
        if (ni < nodes.length) {
          nodes[ni].gv_x = nn.gv_x;
          nodes[ni].gv_y = nn.gv_y;
        }else {
          nodes.push(nn);
        }
      });

      data.links.forEach(function(nl, ni) {
        var link_id = nl.source + '_' + nl.target;
        if (linksDict[link_id] === undefined) {
          links.push(nl);
          linksDict[link_id] = true;
        }
      });
      restart();
    },
    error:  function(xhr, sts, err) {
      alert(xhr.responseText);
      console.log(xhr.responseText);
    }
  });
}


// function to retrieve viz data for a session and visualize
function addViz(id, url) {
  addVizUrl = url;
  $.ajax({
    url: addVizUrl,
    data: {id: id},
    success: function(data, sts, xhr) {
      addNodesAndLinks(data);
    },
    error:  function(xhr, sts, err) {
      alert(xhr.responseText);
      console.log(xhr.responseText);
    }
  });
}


// function to extract text from data used for node label
function get_text(d) {
  if (showHumanReadable) {
    if (d.doc['prov:type'] === undefined) {
      if (d.prov_type === undefined)
        var t = d.concept;
      else
        var t = 'prov:' + d.prov_type.charAt(0).toUpperCase() + d.prov_type.slice(1);
    }else {
      if (d.doc['prov:type']['$'] === undefined) var t = d.doc['prov:type'];
      else var t = d.doc['prov:type']['$'];
    }
    if (d.prov_type == "agent") {
      if (t == "prov:SoftwareAgent")
        return '(prov:SoftwareAgent) ' + d.doc['hysds:host'] + '/' + d.doc['hysds:pid'];
      else if (t === undefined) t = 'prov:Agent'
    }
    if (d.type == "e2e_related" || d.type == "a2e_related" || d.type == "associated" 
        || d.type == "used" || d.type == "wasGeneratedBy" ) var label = "";
    else {
      var label = d.doc['prov:label'] !== undefined ? d.doc['prov:label'] :
                  d.doc['dcterms:title'] !== undefined ? d.doc['dcterms:title'] : d.id;
    }
    return '(' + t + ') ' + label;
  }else
    return d.id;
}


// function to extract text from data used for path label
function get_path_text(d) {
  return d.concept;
}


// function to draw and update visualization
function restart() {
  // create paths
  if (allGroup == null) allGroup = svg.append("g"); 
  if (pathGroup == null) pathGroup = allGroup.append("g");
  var path = pathGroup.selectAll("path")
      .data(force.links())
    .enter().append("path")
      .attr("id", function(d) { return d.source + "_" + d.target; })
      .attr("class", function(d) { return "link " + d.type; })
      .attr("marker-end", function(d) { return "url(#" + d.type + ")"; })
      .on("mouseover", toggleTip)
      .on("mouseout", toggleTip);
  
  // add agent node
  if (agentGroup == null) agentGroup = allGroup.append("g");
  var agent = agentGroup.selectAll("polygon")
      .data(force.nodes().filter(function(d) {
          if (d.prov_type == "agent") return true;
          return false;
      }))
    .enter().append("polygon")
      .attr("points", "0,0 " + polyLength*2 + ",0 " + polyLength + "," + polyLength*2)
      .on("click", click_dispatcher)
      //.filter(function(d) {
      //    if (hideLabel[d.prov_type]) return true;
      //    return false;
      //})
      .on("mouseover", toggleTip)
      .on("mouseout", toggleTip);
  //agentGroup.selectAll("polygon").call(force.drag);
  
  // add activity nodes
  if (actsGroup == null) actsGroup = allGroup.append("g");
  var acts = actsGroup.selectAll("circle")
      .data(force.nodes().filter(function(d) {
          if (d.prov_type == "activity") return true;
          return false;
      }))
    .enter().append("circle")
      .attr("r", radiusLength)
      .on("click", click_dispatcher)
      //.filter(function(d) {
      //    if (hideLabel[d.prov_type]) return true;
      //    return false;
      //})
      .on("mouseover", toggleTip)
      .on("mouseout", toggleTip);
  //actsGroup.selectAll("circle").call(force.drag);
  
  // add entity nodes
  if (entsGroup == null) entsGroup = allGroup.append("g");
  var ents = entsGroup.selectAll("rect")
      .data(force.nodes().filter(function(d) {
          if (d.prov_type == "entity") return true;
          return false;
      }))
    .enter().append("rect")
      .attr("class", "entity")
      .attr("width", rectLength)
      .attr("height", rectLength)
      .on("click", click_dispatcher)
      //.filter(function(d) {
      //    if (hideLabel[d.prov_type]) return true;
      //    return false;
      //})
      .on("mouseover", toggleTip)
      .on("mouseout", toggleTip);
  //entsGroup.selectAll("rect").call(force.drag);
  
  // add groups to activities and agent for text nodes
  if (nodeTextGroup == null) nodeTextGroup = allGroup.append("g");
  var nodeText = nodeTextGroup.selectAll("g")
      .data(force.nodes())
    .enter().append("g");
  
  // A copy of the node text with a thick white stroke for legibility.
  nodeText.append("text")
      .attr("x", 8)
      .attr("y", ".31em")
      .attr("class", "shadow")
      .attr("node_idx", function(d, i) { return i; })
      .text(get_text);
  
  nodeText.append("text")
      .attr("x", 8)
      .attr("y", ".31em")
      .attr("node_idx", function(d, i) { return i; })
      .text(get_text);
      
  // hide text for all entities, agents, and activities
  nodeText.selectAll("text")
    .filter(function(d) {
      if (hideLabel[d.prov_type]) return true;
      else return false;
    })
    .attr("class", "hidden");
  
  // add groups to paths for text nodes
  if (pathTextGroup == null) pathTextGroup = allGroup.append("g");
  var pathText = pathTextGroup.selectAll("g")
      .data(force.links())
    .enter().append("g");
  
  // A copy of the path text with a thick white stroke for legibility.
  pathText.append("text")
      .attr("x", 8)
      .attr("y", ".31em")
      .attr("class", "shadow")
      .attr("path_idx", function(d, i) { return i; })
      .text(get_path_text);
  
  pathText.append("text")
      .attr("x", 8)
      .attr("y", ".31em")
      .attr("path_idx", function(d, i) { return i; })
      .text(get_path_text);
      
  // hide text for all paths
  pathText.selectAll("text")
    .filter(function(d) {
      if (hideLabel.path) return true;
      else return false;
    })
    .attr("class", "hidden");
  
  // resize
  resize();
  d3.select(window).on("resize", resize);
  forceEnabled = true;
  $('#toggle_force').addClass("btn-success");
  enableForce();
  setTimeout(function() {
    force.start();
  }, 500);
  
}


// handler to dispatch to either the click or dblclick handler
function click_dispatcher(d) {
  if (d3.event.defaultPrevented) return; // prevent drag from sending click event
  if (clickedOnce) {
    dblclick(d);
  }else {
    timer = setTimeout(function() {
      click(d);
    }, 300);
    clickedOnce = true; 
  }
}


// handler to open up info window of a node
function click(d) {
  clickedOnce = false;
  //clickedNode = d3.select(this);
  //console.log("click");
  //console.log(clickedNode);
  //console.log(d);
  var doc = d.doc;
  var html = "<table class='table table-striped table-bordered' id='prov_es_info_tbl'>";
  var title = d.id;
  for (var k in doc) {
    if (doc.hasOwnProperty(k)) {
      //console.log(k, doc[k]);
      if (k === "prov:label") title = doc[k];
      if (doc[k].constructor === Array) {
        var val = doc[k].join(", ");
      }else {
        var val = doc[k];
      }
      html += "<tr><td><b>" + k + "</b></td><td>" + val + "</td></tr>";
    }
  }
  html += "</table";
  $('#prov_es_info_modal_label').text(title);
  //var json_str = JSON.stringify(d.doc, null, '  ');
  //$('#prov_es_info_text').html('<pre>' + json_str + '</pre>');
  $('#prov_es_info_text').html(html);
  $('#prov_es_info_tbl').linkify();
  $('#prov_es_info_modal').modal('show').css({'left': set_left_margin});
}


// handler to search for lineage of a double-clicked node
function dblclick(d) {
  clickedOnce = false;
  clearTimeout(timer);
  $.ajax({
    url: addVizUrl,
    data: { id: d.id, lineage: true },
    success: function(data, sts, xhr) {
      addNodesAndLinks(data);
    },
    error: function(xhr, sts, err) {
      //console.log(xhr);
      alert("Error: " + xhr.responseText);
    }
  });
}
