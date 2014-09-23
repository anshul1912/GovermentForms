function chat_functionalities() {
    // Messaging
    // Function reads text from chat input and appends to chat message

    $("input.input_text").on("keydown", function(event) {
        if (event.which == 13)
        {
            if ($(this).parent("div").find(".input_text").val() != "")
            {
              var tid = $(this).parent('div').parent('div').attr('id').split('_')[1];
              ws_ticket[tid].ws.send($(this).val());
              // POST comment here

              $.post('/agent/tickets/view?ticket=' + tid, {
                chat: $(this).val(),
                tid: tid,
                _xsrf: _xsrf
              });

              // end POST comment
              $(this).parent("div").parent("div").find("div.chat_message").find('ul').append("<li>You: " + $(this).parent("div").find(".input_text").val() + "</li>");
              $(this).parent("div").find(".input_text").val("");
              $(this).parent("div").parent("div").find("div.chat_message").scrollTop( $(this).parent("div").parent("div").find("div.chat_message").scrollTop() + $(this).parent("div").parent("div").find("div.chat_message").children().last().position().top );
            }

        }
    });


    //Close Chat Window
    // Function on button click closes the chat window by removing the chat div
    $("a.chat_close").on("click", function(e){
      e.preventDefault();
      var tid = $(this).parent("div").parent("div").parent("div").attr('id').split('_')[1];
      ws_ticket[tid].ws.close();
      delete ws_ticket[tid];
      saveTState();
      $(this).parent("div").parent("div").parent("div").remove();
    });

    $('.btn-open').on('click', function(e){
      e.preventDefault();
      var tid = $(this).parent("div").parent("div").parent("div").attr('id').split('_')[1];

      $(this).addClass('disabled');
      $(this).text('Please wait ...');

      $.post('/agent/tickets/view', {
        comment: 'Changing ticket state',
        status: 'open',
        _xsrf: _xsrf,
        tid: tid,
        notchat: true
      }).done(function(e){
        alert('The ticket state was successfully changed!');
        ws_ticket[tid].ws.close();
        delete ws_ticket[tid];
        saveTState();
        $('#chatBox_' + tid).parent("div").remove();
      }).fail(function(e){
        alert('An error was encountered');
        $('#chatBox_' + tid).find(".btn-open").removeClass('disabled');
        $('#chatBox_' + tid).find(".btn-open").text('Open');
      });
    });

    $('.btn-hold').on('click', function(e){
      e.preventDefault();
      var tid = $(this).parent("div").parent("div").parent("div").attr('id').split('_')[1];

      $(this).addClass('disabled');
      $(this).text('Please wait ...');

      $.post('/agent/tickets/view', {
        comment: 'Changing ticket state',
        status: 'hold',
        _xsrf: _xsrf,
        tid: tid,
        notchat: true
      }).done(function(e){
        alert('The ticket state was successfully changed!');
        ws_ticket[tid].ws.close();
        delete ws_ticket[tid];
        saveTState();
        $('#chatBox_' + tid).parent("div").remove();
      }).fail(function(e){
        alert('An error was encountered');
        $('#chatBox_' + tid).find(".btn-hold").removeClass('disabled');
        $('#chatBox_' + tid).find(".btn-hold").text('Hold');
      });
    });

    $('.btn-close').on('click', function(e){
      e.preventDefault();
      var tid = $(this).parent("div").parent("div").parent("div").attr('id').split('_')[1];

      $(this).addClass('disabled');
      $(this).text('Please wait ...');

      $.post('/agent/tickets/view', {
        comment: 'Changing ticket state',
        status: 'close',
        _xsrf: _xsrf,
        tid: tid,
        notchat: true
      }).done(function(e){
        alert('The ticket state was successfully changed!');
        ws_ticket[tid].ws.close();
        delete ws_ticket[tid];
        saveTState();
        $('#chatBox_' + tid).parent("div").remove();
      }).fail(function(e){
        alert('An error was encountered');
        $('#chatBox_' + tid).find(".btn-close").removeClass('disabled');
        $('#chatBox_' + tid).find(".btn-close").text('Close');
      });
    });

    //Minimize Maximize Chat
    // Function on button click minimizes the chat window
    $("a.chat_min_max").on("click", function(e){
        e.preventDefault();
        $(this).parent("div").parent("div").parent("div").find("div.chat_settings").toggle();
        $(this).parent("div").parent("div").parent("div").find("div.chat_message").toggle();
        $(this).parent("div").parent("div").parent("div").find("div.chat_input").toggle();
        $(this).parent("div").find("a.chat_min_max").toggle();
    });

}

function unBindEventListeners() {
    $("input.input_text").unbind();
    $("div.chat_controls > a.chat_close").unbind();
    $("div.chat_controls > a.chat_min_max").unbind();
}

// Add Chat Window
// NOTE: Better way to add nested html can be found on http://stackoverflow.com/questions/11173589/best-way-to-create-nested-html-elements-with-jquery. Use it if this one acts buggy.
function addTalk(title, ticket_id, callback){
  if ($('div.chat_container').length > 2) {
    return false;
  }

  if ($('div#chatBox_' + ticket_id).length > 0) {
    return false;
  }

  $('<div id="chatBox_' + ticket_id + '" class="chat_container"> <div class="chat_title"> <div class="identifier">' + title  + '</div> <div class="chat_controls"> <!--close button--> <a href="#" class="chat_close" style="float:right;"> <img src="/static/talkgadget/portlet-remove-icon-white.png" width="12"></a> <span style="float:right;">&nbsp;</span> <span style="float:right;">&nbsp;</span> <span style="float:right;">&nbsp;</span>  <!--minimize--> <a class="chat_min_max" href="#" style="float:right;"> <img src="/static/talkgadget/portlet-collapse-icon-white.png" width="15"></a> <!--maximize--> <a class="chat_min_max" href="#" style="float:right; display:none"> <img src="/static/talkgadget/portlet-expand-icon-white.png" width="15"></a> </div> </div> <div class="chat_settings"> <div class="btn-group btn-group-solid"> <button type="button" class="btn btn-sm green btn-open"><i class="fa fa-folder-open-o"></i> Open</button> <button type="button" class="btn btn-sm purple btn-hold"><i class="fa fa-clock-o"></i> Hold</button> <button type="button" class="btn btn-sm red btn-close"><i class="fa fa-folder-o"></i> Close</button>  </div> </div> <div class="chat_message"> <ul></ul> </div> <div class="chat_input"> <input class="form-control input_text" type="text"> </div> </div>').appendTo("div.chat");
  unBindEventListeners();
  chat_functionalities();
  if (callback != undefined) {
    callback(ticket_id, title);
  }
}

$(document).ready(function(){
  chat_functionalities();
  var q;
  try {
    q = JSON.parse($.cookie('ws_tickets'));
    for (var key in q) {
      addTalk(q[key], key, openWS);
    }
  } catch (e) {
    return false;
  }
});


  var ws; // for Agent Central
  var ws_ticket = {}; // ..

  function wsconnect() {

    var ws_proto;
    if (location.protocol == 'https:') {
      ws_proto = 'wss';
    } else {
      ws_proto = 'ws';
    }

    ws = new WebSocket(
      ws_proto +
      "://" +
      location.href.split('/')[2] +
      "/wsagent"
    );

    ws.onopen = function (evt) {
      console.log('[Agent]: Now connected to Agent central');
    }

    ws.onmessage = function (evt) {
      var q;
      console.log('[Agent]: Received message -> ' + evt.data);
      try {
        q = JSON.parse(evt.data);
      } catch(e) {
        return false;
      }

      if (q != undefined) {
        var alreadyThere = false;
        if (q.type == 'ticket') {
          $('#ticket_list tr').each(function (index, row) {
            if (q.message.id == parseInt($(row).find('td.idCell').text())) {
              alreadyThere = true;
            }
          });

          if (!alreadyThere) {
            $('#ticket_list').append("<tr><td class='idCell'>" + q.message.id + "</td><td><a class='liveTicket' data-id='" + q.message.id +"' href='/agent/tickets/view?ticket=" + q.message.id + "'>" + q.message.title + "</a></td><td>" + q.message.timestamp + "</td><td>live</td></tr>");


            liveTC();
          }

          if (q.status != 'live') {
            // alert('Status not live for ' + q.message.id + '!');
            $('#ticket_list tr').each(function (index, row) {
              if (q.message.id == parseInt($(row).find('td.idCell').text())) {
                $(row).remove();
              }
            });
          }

        }
      }
    }

    ws.onclose = function (evt) {
      wsconnect();
      // console.log('The websocket connection closed.');
    }
  }

  function liveTC() {
    $('.liveTicket').unbind();
    $('.liveTicket').on('click', function(e) {
      e.preventDefault();
      var title = $(this).text().slice(0, 20) + ' ...';
      var tid = $(this).data('id');
      addTalk(title, tid, openWS);
    })
  }

  function saveTState() {
    var q = {};
    for (var key in ws_ticket) {
      q[key] = ws_ticket[key].title;
    }

    $.cookie('ws_tickets', JSON.stringify(q), {path: '/'});
  }

  function openWS(ticket_id, ticket_title) {
    var ws_proto;
    if (location.protocol == 'https:') {
      ws_proto = 'wss';
    } else {
      ws_proto = 'ws';
    }

    ws_ticket[ticket_id] = {}
    ws_ticket[ticket_id].title = ticket_title;

    ws_ticket[ticket_id].ws = new WebSocket(
      ws_proto +
      "://" +
      location.href.split('/')[2] +
      "/wsticket/" + ticket_id
    );

    ws_ticket[ticket_id].ws.onmessage = function(evt) {
      $('#chatBox_' + ticket_id).find('div.chat_message').find('ul').append("<li>" + evt.data + "</li>");
      $('#chatBox_' + ticket_id).find('div.chat_message').scrollTop($('#chatBox_' + ticket_id).find('div.chat_message').innerHeight());
    };

    saveTState();
  }

  $(document).ready(function(){
    wsconnect();
    liveTC();
  });
