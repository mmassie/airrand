/* Author: 

*/
$(function(){

    window.saveQueue = 0;
   // handle form to add a new task
   $('#addform').submit(function(event){
       event.preventDefault();
       var validForm = true;
       $('#addformerror').css({
           opacity:0
       },{
           queue:false
       }).html('&nbsp;');

       var data = {
           whatinput: $('#whatinput').val(),
           whereinput: $('#whereinput').val()
       }

       if ($('#whatinput').hasClass('placeholder')||(!jQuery.trim(data.whatinput))){
           validForm = false;
           $('#addformerror').text("Please enter your task");
       }else if($('#whereinput').hasClass('placeholder')||(!jQuery.trim(data.whereinput))){
           validForm = false;
           $('#addformerror').text("Please enter a location");
       }
       if (!validForm){
           $('#addformerror').animate({
               opacity:1
           },{
               queue:false
           }).delay(800).animate({
               opacity:0
           });

           return;
       }

       $.getJSON('/json/addTask', data, function(data) {
           if(data.success){
               $('#whatinput').val('').blur();
               //$('#whereinput').val('').blur();
               var taskRow = $('#newTask').tmpl(data).prependTo('#todotable tbody').removeClass('animate');
               $('#whatinput').focus();
           }
       });



   });



   // build our fake dropdown
   $('.dropdown').bind('click focus',function(event){
       event.preventDefault();
       $('#homedropdown').toggleClass('hidden');
       $('#homedropdown a.selected').focus();
   });
   $('#whereinputselect').change(function(){
       $('#whereinput').val($('#whereinputselect').val());
   });
   $('.dropdown_wrapper ul a').click(function(event){
       event.preventDefault();
       var selectedText = $(this).text();
       $('#homedropdown').addClass('hidden').find('a selected').removeClass('selected');
       $(this).addClass('selected');
       $('.dropdown').text(selectedText).removeClass('placeholder');
       $('#whereinput').val(selectedText);
       $('#addform').find('button').focus();
   }).keydown(function(e){
       e.preventDefault();
      if(e.keyCode==40||e.keyCode==39){
          //move down list
          $(this).parent().next().find('a').focus().addClass('selected');
          $(this).removeClass('selected');
      }else if(e.keyCode==38||e.keyCode==37){
          //move up list
          $(this).parent().prev().find('a').focus().addClass('selected');
          $(this).removeClass('selected');
      }else if(e.keyCode==32){
          $(this).click();
      }
   });;




   // handle making task complete
   $('#todotable input.checkbox').live('click',function(event){

       var row = $(this).closest('tr');
       var status = 1; // the status we are changing towards, 1 -> live status, 2 -> finished
       if(!row.hasClass('finished')){
           status = 2
       }
       var checkbox = $(this)
       var taskKey = checkbox.attr('id');
       var data = {
           task:taskKey,
           status:status
       }

        $(window).trigger('startSaving');

        row.animate({
           opacity:0
        },{
           complete:function(){
                $(window).trigger('toggleRow',[status,row]);
           }
        });

        if($(this).val()!="demo"){
           $.getJSON('/json/finishTask', data, function(data){
              if(data.success){
                $(window).trigger('doneSaving')
              }
           });
       }else{
           log('in demo mode');
        $(window).trigger('doneSaving');
       }


   });

   // 'toggleRow' function when hitting checkbox
   $(window).bind('toggleRow',function(event,status,row){
       row.detach()
       row.css('opacity',1).addClass('animate').toggleClass("finished").toggleClass('active');
       if (status==2){
           var lastActive = $('tr.active:last');
           if(lastActive.length){
             lastActive.after(row)
           }else{
             row.prependTo('#todotable tbody');
           }

       }else{
           row.prependTo('#todotable tbody');
       }
       row.removeClass('animate')
   });

   $(window).bind('startSaving',function(){
      window.saveQueue++;
      $('#saving').fadeIn();
   });

   $(window).bind('doneSaving',function(){
      window.saveQueue--;
      if(window.saveQueue<1){
          window.saveQueue=0;
          $('#saving').fadeOut();
      }
   });


   // handle delete task event
   $('a.deleteLink').live('click',function(event){
       event.preventDefault();

       var deleteLink = $(this)
       var taskKey = deleteLink.attr('data-key');
       var data = {
           task:taskKey
       }
       
       $.getJSON('/json/deleteTask', data, function(data) {
           if(data.success){
               var deleteRow = $('#'+data.task).closest('tr');
               deleteRow.animate({
                   opacity:0
               },
               {
                   complete:function(){
                       deleteRow.closest('tr').remove();
                   }
               });
           }
       });
   });

   /*------------------------------------------------------------------*/
   // couples stuff
   $('.cancelCouple').click(function(event){
      event.preventDefault();
      var action,parentDiv = $(this).parent();
      var inviteCode = parentDiv.attr("data-inviteCode");
      if(parentDiv.hasClass('confirmed')){
          action = "removePartner";
      }else if (parentDiv.hasClass('received')){
          action = "rejectInvite";
      }else if(parentDiv.hasClass('sent')){
          action = "cancelInvite"
      }
      var data = {
          'inviteCode':inviteCode,
          'action':action
      }
      log(inviteCode);
      log(action)
      $.getJSON('/json/handleInvite', data, function(data) {

      });
   });
   $('.coupleAccept').click(function(event){
      event.preventDefault();
      var inviteCode = $(this).attr("data-inviteCode");
      var data = {
          'inviteCode':inviteCode,
          'action':'acceptInvite'
      }
      log(inviteCode);
      $.getJSON('/json/handleInvite', data, function(data) {
        if(!data.success){
            alert(data.reason);
            return;
        }
        switch(data.action){
            case "removePartner":

            case "rejectInvite":

            case "cancelInvite":
        }
      });
   });
   // end couples stuff
   /*------------------------------------------------------------------*/


   // get rid of scrollbar
   window.scrollTo(0,1);

   // do the iphone bookmark stuff if this is the homepage
   if($('#main').hasClass('home')){

        window.setTimeout(function() {
        var bubble = new google.bookmarkbubble.Bubble();

        var parameter = 'bmb=1';

        bubble.hasHashParameter = function() {
          return window.location.hash.indexOf(parameter) != -1;
        };

        bubble.setHashParameter = function() {
          if (!this.hasHashParameter()) {
            window.location.hash += parameter;
          }
        };

        bubble.getViewportHeight = function() {
          window.console.log('Example of how to override getViewportHeight.');
          return window.innerHeight;
        };

        bubble.getViewportScrollY = function() {
          window.console.log('Example of how to override getViewportScrollY.');
          return window.pageYOffset;
        };

        bubble.registerScrollHandler = function(handler) {
          window.console.log('Example of how to override registerScrollHandler.');
          window.addEventListener('scroll', handler, false);
        };

        bubble.deregisterScrollHandler = function(handler) {
          window.console.log('Example of how to override deregisterScrollHandler.');
          window.removeEventListener('scroll', handler, false);
        };

        bubble.showIfAllowed();
        }, 1000);

   }
});