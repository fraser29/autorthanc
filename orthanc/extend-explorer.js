
$('#series').live('pagebeforecreate', function() {

    var b = $('<a>')
      .attr('data-role', 'button')
      .attr('href', '#')
      .attr('data-icon', 'search')
      .attr('data-theme', 'e')
      .text('Send series to Urography pipeline');
  
    b.insertBefore($('#series-delete').parent().parent());
    b.click(function() {
      if ($.mobile.pageData) {
        var seriesID = $.mobile.pageData.uuid;
  
        window.open('/uropipeline/' + seriesID);
        // window.open('/series/'+seriesID+'/archive?filename=/Volume/download.zip');
        // TODO - remove this unless can think of a way to update on fly. 
        // TODO - maybe have one to manually force run all automation
      }
    });
  });
  