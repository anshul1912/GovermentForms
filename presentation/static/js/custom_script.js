$(document).on('ready', function()
{
   var names = [];
   var com_name;
        // tell Select2 to use the property name for the text
    function Select2_function(item)
    {
      return item.name;
    };
    $.getJSON('/public?companies=yes',function(data)
    {
      for(var i = 0; i < data.length; i++)
      {
            names.push({"id":data[i].name,"name":data[i].name});
      }
    });


  $("#search_box").select2
  ({
          data:{ results: names, text: 'name' },
          placeholder:"Search By Company",
          formatSelection: Select2_function,
          formatResult: Select2_function
  });

  $('#loadmore').on('click', function(e)
  {
      e.preventDefault();
      var $btn = $(this);
      $btn.button('loading');
      var ts = $(this).data('ts');
      loadMore(ts,com_name);
  });

  $('#search_button').on('click',function(e)
  {
    com_name=$('#search_box').val();
    if(com_name != "")
    {
        filter(com_name);
    }
    else
    {
      alert("Please select a Company");
    }

  });

});

function loadMore(ts,com_name)
{
      var q = encodeURIComponent(ts);
      var json_file;
      if(com_name == undefined)
      {
         json_file = '/public?ts=' + q + '&json=yes&r=2';
      }
      else
      {
        json_file = '/public?ts=' + q + '&json=yes&r=2&company='+com_name;
      }
      $.getJSON(json_file).done(function(data)
      {
        if(data.length == 0)
        {
          $('#loadmore').hide();
        }
        else
        {
          $('.btn').button('reset');
          for (var i = 0; i < data.length; i++)
          {
            $('#flist').append('<div class="container"><div class="fadeIn" style="display:none"><div class="row"><div class="col-md-12 col-sm-12"><h2><a href="/public/' + data[i][5] + '">' + data[i][0] + ' - ' + data[i][2] + '</a></h2><h4>' + data[i][2] + '</h4><ul class="blog-info"><li><i class="fa fa-tags"></i> Ticket logged by : ' + data[i][3] + '</li><li><i class="fa fa-calendar"></i> Tickets logged on : ' + data[i][4] + '</li></ul></div></div></div></div>');
          }
          $('.fadeIn').slideDown();
          var newts = data[data.length - 1][4];
          $('#loadmore').data('ts', newts)
        }
      });
}

function filter(com_name)
{
  var q = encodeURIComponent(com_name);
  $('.btn').button('reset');
  $('#loadmore').show();
  $('#flist').text("");
  $.getJSON('/public?company=' + q + '&json=yes', function(data)
  {
    for (var i = 0; i < data.length; i++)
    {
      $('#flist').append('<div class="container"><div class="row"><div class="col-md-12 col-sm-12"><h2><a href="/public/' + data[i][5] + '">' + data[i][0] + ' - ' + data[i][2] + '</a></h2><h4>' + data[i][2] + '</h4><ul class="blog-info"><li><i class="fa fa-tags"></i> Ticket logged by : ' + data[i][3] + '</li><li><i class="fa fa-calendar"></i> Tickets logged on : ' + data[i][4] + '</li></ul></div></div></div>');
    }
  });
}

