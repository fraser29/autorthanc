$('#study').live('pagebeforecreate', function() {

    var b = $('<a>')
      .attr('data-role', 'button')
      .attr('href', '#')
      .attr('data-icon', 'search')
      .attr('data-theme', 'e')
      .text('Force Automation Action');
  
    b.insertBefore($('#study-delete').parent().parent());
    b.click(function() {
      if ($.mobile.pageData) {
        var study = $.mobile.pageData.uuid;
  
        window.open('/orthanc/forcestablesignal/' + study);
      }
    });
  });