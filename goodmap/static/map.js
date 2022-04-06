 $.ajaxSetup({
    async: false
});

 let text     = '[{"name": "PCK","position": [17.05, 51.1] }]';

 var data     = $.getJSON("/data").responseJSON
// var data     = JSON.parse(text);
 console.log(data)
//  $.ajaxSetup({
//    async: true
//});

 var points   = data.map(x => new ol.Feature({
     name: x.name,
     geometry: new ol.geom.Point(ol.proj.fromLonLat(x.position))
 }))

 var myStyle = new ol.style.Style({
   image: new ol.style.Circle({
     radius: 7,
     fill: new ol.style.Fill({color: 'black'}),
     stroke: new ol.style.Stroke({
       color: [255,0,0], width: 2
     })
   })
 })

 var map = new ol.Map({
     controls: ol.control.defaults({attribution: true}),
     layers: [
         new ol.layer.Tile({
             source: new ol.source.OSM()
         })
     ],
     target: 'map',
     view: new ol.View({
         center: ol.proj.fromLonLat([17.05, 51.1]),
         maxZoom: 18,
         zoom: 12
     })
 });
     var layer = new ol.layer.Vector({
       style: myStyle,
       source: new ol.source.Vector(
       {
         features: points
       })
     });
 map.addLayer(layer);
