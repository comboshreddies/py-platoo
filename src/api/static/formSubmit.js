function adjustForm() {
    var form = document.getElementById('addMemo');
    function XHRRefreshMemos() {
        var xhr = new XMLHttpRequest();
	xhr.responseType = 'json';
	xhr.open('GET','/memos/v1');
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.send();
	xhr.onreadystatechange = function() {
	    if (xhr.readyState == XMLHttpRequest.DONE) {
	        var memos = document.getElementById('memos');
		console.log(xhr.response);
		count = xhr.response['count'];
		var new_memo_content = '';
		var items = xhr.response['items'];
		var item_count = items.length;
		for(var i=0;i<item_count;i++) {
		    new_memo_content += '<hr/> <!-- ' + items[i]['uuid'] + ' --> ' + items[i]['memo'] + "\n"
		} 
                memos.innerHTML = new_memo_content;
                var counter = document.getElementById('counter');
                counter.innerHTML = count;
	    }
	}
    }
    function XHRSubmit(event){
	event.preventDefault();
        var xhr = new XMLHttpRequest();
        var formData = new FormData(form);
	xhr.responseType = 'json';
        xhr.open('POST','/memos/v1');
        xhr.setRequestHeader("Content-Type", "application/json");
	formObject = Object.fromEntries(formData);
	console.log(formObject);
	jsonPayload = JSON.stringify(Object.fromEntries(formData));
        xhr.send(jsonPayload);
        xhr.onreadystatechange = function() {
            if (xhr.readyState == XMLHttpRequest.DONE) {
		memo = formObject['memo'];
		console.log(memo);
                form.reset();
		var submitStatus = document.getElementById('submitStatus');
		if ( submitStatus ) submitStatus.innerHTML = 'inserted: ' + xhr.response['uuid'];
		var memos = document.getElementById('memos');
		memos.innerHTML = '<hr/> <!-- ' + xhr.response['uuid'] + ' --> ' + memo + "\n" + memos.innerHTML;
		var counter = document.getElementById('counter');
		counter.innerHTML = parseInt(counter.innerHTML) + 1;
            }
        }
        return false;
    }
    form.addEventListener("submit", XHRSubmit);
    if (window.location.pathname == '/dynamic') {
        XHRRefreshMemos();
	}
}

window.onload = adjustForm;
