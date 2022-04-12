 window.onload=function(){
    var search_results = {};
    var captured_domains = []
    var current_welcome_page_index = 0

    $("#welcome-popup").css("visibility","visible")
    setMainPageActive(false)

    $(".searchText").on('keyup', function(){
        searchText = $(".searchText").val()
        search(searchText)
     })

    $(".chatting").on('keyup', function(){
        typing();
     })

     $('.next-image').click(function(e) {
        if (current_welcome_page_index < 2 && current_welcome_page_index >= 0){
            $('#img'+current_welcome_page_index).css("display","none")
            current_welcome_page_index++
            $('#img'+current_welcome_page_index).css("display","flex")
        }
     })

    $('.previous-image').click(function(e) {
         if (current_welcome_page_index <= 2 && current_welcome_page_index >= 1){
            $('#img'+current_welcome_page_index).css("display","none")
            current_welcome_page_index--
            $('#img'+current_welcome_page_index).css("display","flex")
        }
     })

     $('.clearbtn').click(function (e) {
        e.preventDefault();
        $('.chatting').val('');
        $(".voldemort ul").empty();
        $(".accordion-row ul").empty();
    });

     $('#submit').click(function (e) {
        e.preventDefault();
        $('#chatbot-form').submit();
    });

     $('#chatbot-form').submit(function (e) {
        e.preventDefault();    
        var message = $('.chatting').val().trim();
        if (message == "") { 
            return 
        }
    
        chatActive(false)
        $('.chatting').val('')
        typing();
        $(".voldemort ul").append('<li class="outgoing bubble"><p class="textmessage">' + message + '</p></li>')
        
        $(".voldemort ul").append('<li class="incoming bubble tdelete"><div class="typing"><div class="ellipsis one"></div><div class="ellipsis two"></div><div class="ellipsis three"></div></div></li>')
        $.ajax({
            type: "POST",
            url: "/ask",
            data: {"messageText":message},
            success: function (response) {
                removeFadeOut($(".incoming.bubble.tdelete")[0], 100)
                $(".voldemort ul").append('<li class="incoming bubble"><p class="textmessage">' + response.answer + '</p></li>')
                captured_domains = unique(captured_domains.concat(response.captured_domains))
                chatActive(true)
                if (response.answer.startsWith("This is the hierarchy I found")){
                    $(".select-btn").addClass("animate-flicker")
                }
            },
            error: function (error) {
                removeFadeOut($(".incoming.bubble.tdelete")[0], 100)
                $(".voldemort ul").append('<li class="incoming bubble"><p class="textmessage"> Error occured, please try again</p></li>')
                chatActive(true)
            }
        });
        
    });
    
    $(".feedback-btn").on('click', function(){
        $(".feedback-popup").css("visibility","visible")
        setMainPageActive(false)
     })

     $(".select-btn").on('click', function(){
        list = $("#domains-from-chat")
        list.empty();
        for (let i=0; i<captured_domains.length; i++){
            list.append('<li><input type="checkbox" id="chatcheckbox'+i+'" value="'+captured_domains[i]+'"><label for="chatcheckbox'+i+'">'+captured_domains[i]+'</label></li>')          
        }
        $(".select-btn").removeClass("animate-flicker")
        $(".domain-selection-popup").css("visibility","visible")
        setMainPageActive(false)
     })

     $(".domain-add-btn").on('click', function(){
        custom_domain_text = $('#customeDomain').val().trim()
        if (custom_domain_text ==""){
            return
        }
        items = $(".extra-domains-content ul li")
        id = items.length
        for (let i=0; i<id; i++){
            if (items[i].textContent == custom_domain_text){
                return
            }
        }
        $(".extra-domains-content ul").append('<li><input type="checkbox" id="checkbox'+id+'" value="'+custom_domain_text+'"><label for="checkbox'+id+'">'+custom_domain_text+'</label></li>')          
        $('#customeDomain').val('')
    })
    
    function unique(arr) {
        const unique = [...new Set(arr.map(item => item))];
      return unique;
    }
    
    $(".domain-selection-submit").on('click', function(){
        keywords=[]
        selected_domains = $(".domain-selection-content input:checked")
        for (let i=0; i<selected_domains.length; i++){
            keywords.push(selected_domains[i].value)
        }
        keywords = unique(keywords)
        
        if (keywords.length == 0){
            alert("please select at least one domain")
            return 
        }
        $(".execute-search").prop('disabled', true)
        $(".execute-search").html("Searching...")
        $(".execute-search").css("background","#777")
        
        $.ajax({
            type: "POST",
            url: "/search",
            data: {"keywords":keywords},
            success: function (response) {
                $(".no-results").css("display","none")
                $(".people").css("display","flex")
                $(".search").css("display","flex")
                $(".domain-selection-popup").css("visibility","hidden")
                $(".execute-search").html("Search")
                $(".execute-search").css("background","#5887ab")
                $('#customeDomain').val('')
                $(".domains-list").empty()
                id = "sr_" + Object.keys(search_results).length
                addSearchResult(id, "Search result " + Object.keys(search_results).length, [], response.articles)
                setMainPageActive(true)
                captured_domains = []
                $(".execute-search").prop('disabled', false)
                $('.clearbtn').click()
                $(".popup-title-domains").html(keywords.join(", "))
                $("#"+id).click()
            },
            error: function (error) {
                captured_domains = []
                $(".domains-list").empty()
                $('#customeDomain').val('')
                $(".execute-search").html("Search")
                $(".execute-search").css("background","#5887ab")
                $(".execute-search").prop('disabled', false)
                $('.clearbtn').click()
                setMainPageActive(true)
            }
        });
     })

     $(".domain-close").on('click', function(){
        $(".domain-selection-popup").css("visibility","hidden")
        setMainPageActive(true)
     })
     
     $(".feedback-close").on('click', function(){
        $(".feedback-popup").css("visibility","hidden")
        setMainPageActive(true)
     })

     $(".md-close").on('click', function(){
        $("#popup").css("visibility","hidden")
        $(".feedback-btn").addClass("animate-flicker")
        setMainPageActive(true)
    })

    $(".close-welcome-btn").on('click', function(){
        $("#welcome-popup").css("visibility","hidden")
        setMainPageActive(true)
    })
    

    function search(text) {
        text = text.toLowerCase()
        results = $(".person")
        for (let index = 0; index < results.length; index++) {
        if (text == undefined || text == "" || (results[index].textContent.toLowerCase().includes(text))){
            $(results[index]).css("visibility","visible")
            $(results[index]).css("height", "auto")
            /* FIX! */
            $(results[index]).css("padding", "12px 0 12px 12px")
        } else{
            $(results[index]).css("visibility","hidden")
            $(results[index]).css("height", "0px")
            $(results[index]).css("padding", "0px")
        } 
    }
    }

    function addSearchResult(id, title, badges, articles) {
        if (articles == undefined) articles = []
        if (badges == undefined) badges = []
        search_results[id] = {
            "title":title,
            "domains":badges, 
            "badges":badges, 
            "articles":articles, 
        }

        badges_list = ""
        badges.forEach(b => { badges_list += '<li><span class="badge badge-secondary">'+b+'</span></li>' });
        $(".people").append('<li id='+id+' class="person focus"><span class="title">'+title+'</span><div class="domains"><ul>'+badges_list+'</ul></div></li>')
        registerForSearchResultsClickEvents();
    }

    function chatActive(active) {
        if (active){
            $('.chatting').prop("placeholder","Type a message...")
            $('.chatting').prop("disabled", false)
            $('.chat-btn').prop("disabled", false)
            $('.select-btn').prop("disabled", false)
            $('.clearbtn').prop("disabled", false)
        } else {
            $('.chatting').prop("disabled", true)
            $('.chat-btn').prop("disabled", true)
            $('.select-btn').prop("disabled", true)
            $('.clearbtn').prop("disabled", true)
            $('.chatting').prop("placeholder","Processing request, please wait...")
        }
    }

    function setMainPageActive(active) {
        if (!active){
            $(".container").css("pointer-events","none");
            $(".container").css("filter", "blur(3px)");
            $(".aboutme").css("pointer-events","none");
            $(".aboutme").css("filter", "blur(3px)");
        } else {
            $(".container").css("filter", "blur(0px)");
            $(".container").css("pointer-events","auto");
            $(".aboutme").css("filter", "blur(0px)");
            $(".aboutme").css("pointer-events","auto");
        }
    }

    function registerForSearchResultsClickEvents() {
        $(".person").on('click', function(){
            $(this).toggleClass('focus').siblings().removeClass('focus');
            id = $(this).attr('id');
            result = search_results[id];
            updatePopupWindow(id, result.title, result.domains, result.articles);
            $("#popup").css("visibility","visible");
            setMainPageActive(false);
        })
    }

    function updatePopupWindow(id, title, domains, articles) {
        $(".popup-title").val(title);
        $(".popup-title-domains").val(domains);
        $(".accordion-row ul").empty();

        for (let index = 0; index < articles.length; index++) {
            domani_list = '<ul class="accordion-tags">';
            articles[index].keywords.split(",").forEach(b => { domani_list += '<li class="article-result-title-tag">'+b+'</li>' });
            domani_list += "</ul>";
            $(".accordion-row .accordion").append(
                '<li class="accordion-item" id="question'+index+'">\
                    <a class="accordion-link" href="#question'+index+'">\
                        <div class="flex article-result">\
                            <h3 class="article-result-title">'+articles[index].title+'</h3>\
                            '+domani_list+'\
                        </div>\
                        <i class="icon ion-md-arrow-forward"></i>\
                        <i class="icon ion-md-arrow-down"></i>\
                    </a>\
                    <div class="answer">'+createArticleSummary(articles[index])+'\
                    </div>\
                </li>'
            )
        };
    }

    function createArticleSummary(article) {
        return '<section id="skills">\
            <div class="skill-text">\
                <div class="s-box-container">\
                    <div class="skill-box">\
                        <div class="s-box-icon">\
                            <i class="fab fa-html5"></i>\
                        </div>\
                        <div class="s-box-text">\
                            <strong>Summary</strong>\
                            <p>'+article.summary+'</p>\
                        </div>\
                    </div>\
                    <div class="skill-box">\
                        <div class="s-box-icon">\
                            <i class="fab fa-css3-alt"></i>\
                        </div>\
                        <div class="s-box-text">\
                            <strong>Conclusions</strong>\
                            <p>'+article.conclusions+'</p>\
                        </div>\
                    </div>\
                    <div class="skill-box">\
                        <div class="s-box-icon">\
                            <i class="fab fa-js-square"></i>\
                        </div>\
                        <div class="s-box-text">\
                            <strong>Future Work</strong>\
                            <p>'+article.future_work+'</p>\
                        </div>\
                    </div>\
                    <div class="skill-box">\
                        <div class="s-box-icon">\
                            <i class="fab fa-js-square"></i>\
                        </div>\
                        <div class="s-box-text">\
                            <strong>Link</strong>\
                            <p>'+article.url+'</p>\
                        </div>\
                    </div>\
                </div>\
            </div>\
        </section>'
    }

    function dragElement(elmnt) {
        var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        if (document.getElementById(elmnt.id + "header")) {
            // if present, the header is where you move the DIV from:
            document.getElementById(elmnt.id + "header").onmousedown = dragMouseDown;
        } else {
            // otherwise, move the DIV from anywhere inside the DIV:
            elmnt.onmousedown = dragMouseDown;
    }

    function dragMouseDown(e) {
        e = e || window.event;
        e.preventDefault();
        // get the mouse cursor position at startup:
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        // call a function whenever the cursor moves:
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        e = e || window.event;
        e.preventDefault();
        // calculate the new cursor position:
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        // set the element's new position:
        elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
        elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
    }

    function closeDragElement() {
        // stop moving when mouse button is released:
        document.onmouseup = null;
        document.onmousemove = null;
    }
    }

    function typing() {
        if($(".chatting").val() == ""){
            if ($(".outgoing.bubble.tdelete").length) {
                removeFadeOut($(".outgoing.bubble.tdelete")[0], 100)
            }
        } else {
            if ($(".outgoing.bubble.tdelete").length == 0) {
                $(".voldemort ul").append('<li class="outgoing bubble tdelete"><div class="typing"><div class="ellipsis one"></div><div class="ellipsis two"></div><div class="ellipsis three"></div></div></li>')
            }
        }
    }

    function removeFadeOut( el, speed ) {
        var seconds = speed/1000;
        el.style.transition = "opacity "+seconds+"s ease";
    
        el.style.opacity = 0;
        setTimeout(function() {
            el.parentNode.removeChild(el);
        }, speed);
    }

    dragElement(document.getElementById("popup"));
    dragElement(document.getElementById("feedback"));

 }
