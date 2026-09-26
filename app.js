(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const screens = [...document.querySelectorAll('.screen')];
  const categories = [...new Set(window.CARDS.map(card => card.category))];
  const ALL_CATEGORIES = '綜合';
  const categoryEmoji = {'綜合':'🎲','綜合擴充題':'✨','動物':'🐘','食物':'🍕','交通':'🚀','運動':'⚽','職業':'👩‍🚒','日常動作':'👏','生活物品':'🎒','自然幻想':'🌈'};
  const categoryLabel = {'交通':'交通工具','自然幻想':'自然與幻想'};
  const categoryName = category => categoryLabel[category] || category;
  const openMojiPath = emoji => {
    const codepoints=[...emoji].map(character=>character.codePointAt(0).toString(16).toUpperCase().padStart(4,'0')).filter(codepoint=>codepoint!=='FE0F');
    return `assets/openmoji/${codepoints.join('-')}.png`;
  };
  const state = {screen:'home', category:ALL_CATEGORIES, duration:0, queue:[], current:null, correct:[], skipped:[], deadline:0, timerId:null, transitionIds:new Set(), locked:false, audio:null, sound:true, zhuyin:true, lastFocus:null, finished:false, imageRequest:0};

  function loadPreferences(){
    try { state.sound = localStorage.getItem('charades-sound') !== 'false'; } catch (_) { state.sound=true; }
    try { state.zhuyin = localStorage.getItem('charades-zhuyin') !== 'false'; } catch (_) { state.zhuyin=true; }
    updateToggles();
  }
  function savePreference(key,value){ try { localStorage.setItem(key,String(value)); } catch (_) {} }
  function updateToggles(){
    $('sound-toggle').setAttribute('aria-pressed',String(state.sound));
    $('sound-toggle').querySelector('span').textContent=state.sound?'🔊':'🔇';
    $('zhuyin-toggle').setAttribute('aria-pressed',String(state.zhuyin));
    $('zhuyin').hidden=!state.zhuyin;
  }
  function initAudio(){
    if (!state.sound || state.audio) return;
    const AudioContext=window.AudioContext||window.webkitAudioContext;
    if (!AudioContext) return;
    try { state.audio=new AudioContext(); if(state.audio.state==='suspended') state.audio.resume(); } catch (_) { state.audio=null; }
  }
  // 行動瀏覽器只允許在使用者手勢中解鎖 Web Audio。
  document.addEventListener('pointerdown', initAudio, {once:true, passive:true});
  function tone(kind){
    if(!state.sound||!state.audio) return;
    try{
      const now=state.audio.currentTime, osc=state.audio.createOscillator(), gain=state.audio.createGain();
      osc.type='sine'; osc.frequency.setValueAtTime(kind==='correct'?520:kind==='end'?330:260,now);
      if(kind==='correct') osc.frequency.exponentialRampToValueAtTime(780,now+.13);
      gain.gain.setValueAtTime(.0001,now); gain.gain.exponentialRampToValueAtTime(.12,now+.015); gain.gain.exponentialRampToValueAtTime(.0001,now+.19);
      osc.connect(gain).connect(state.audio.destination); osc.start(now); osc.stop(now+.2);
    } catch (_) {}
  }

  function later(fn,ms){ const id=setTimeout(()=>{state.transitionIds.delete(id);fn();},ms);state.transitionIds.add(id);return id; }
  function clearRuntime(){
    if(state.timerId!==null){clearInterval(state.timerId);state.timerId=null;}
    state.deadline=0;state.transitionIds.forEach(clearTimeout);state.transitionIds.clear();state.locked=false;state.imageRequest+=1;
    $('end-dialog').hidden=true;
  }
  function showScreen(id,focus=true){
    if(id!=='game'&&id!=='countdown') clearRuntime();
    document.body.classList.toggle('focus-mode',id==='game'||id==='countdown');
    state.screen=id; screens.forEach(s=>{const active=s.id===id;s.classList.toggle('active',active);s.setAttribute('aria-hidden',String(!active));});
    if(focus) requestAnimationFrame(()=>{const target=$(id).querySelector('h1,h2,button'); if(target){target.setAttribute('tabindex','-1');target.focus({preventScroll:true});}});
    window.scrollTo(0,0);
  }
  function shuffle(items){
    const a=[...items]; for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a;
  }
  function buildCategories(){
    const choices=[ALL_CATEGORIES,...categories];
    $('categories').innerHTML=choices.map((cat,i)=>`<label><input type="radio" name="category" value="${cat}" ${i===0?'checked':''}><span><b aria-hidden="true">${categoryEmoji[cat]}</b>${cat===ALL_CATEGORIES?'不分類別（綜合）':categoryName(cat)}</span></label>`).join('');
  }
  function beginHandoff(){
    state.category=document.querySelector('input[name=category]:checked').value;
    state.duration=Number(document.querySelector('input[name=duration]:checked').value);
    $('round-summary').textContent=`${categoryEmoji[state.category]} ${categoryName(state.category)}・${state.duration?state.duration+' 秒':'無限時間'}`;
    showScreen('handoff');
  }
  function prepareRound(){
    initAudio(); clearRuntime(); state.queue=shuffle(state.category===ALL_CATEGORIES?window.CARDS:window.CARDS.filter(c=>c.category===state.category)); state.correct=[];state.skipped=[];state.current=null;state.finished=false;
    showScreen('countdown',false); let n=3; $('countdown-number').textContent=n;
    const step=()=>{tone('skip');n-=1;if(n>0){$('countdown-number').textContent=n;later(step,700);}else{ $('countdown-number').textContent='開始！'; later(startRound,500); }}; later(step,700);
  }
  function startRound(){
    showScreen('game',false); state.deadline=state.duration?performance.now()+state.duration*1000:Infinity;
    $('timer').textContent=state.duration?formatTime(state.duration):'∞'; $('timer').classList.remove('urgent'); updateScore(); nextCard(true);
    if(state.duration){ state.timerId=setInterval(updateTimer,100); updateTimer(); }
  }
  function formatTime(seconds){const n=Math.max(0,Math.ceil(seconds));return `${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`;}
  function updateTimer(){
    if(state.screen!=='game'||state.finished)return;
    const remaining=(state.deadline-performance.now())/1000; $('timer').textContent=formatTime(remaining); $('timer').classList.toggle('urgent',remaining<=10);
    if(remaining<=0) finishRound('時間到！');
  }
  function updateScore(){ $('score').textContent=`答對 ${state.correct.length}`; }
  function renderCard(){
    const c=state.current;
    const image=$('card-image'), emoji=$('card-emoji');
    const requestToken=++state.imageRequest;
    $('category-badge').textContent=`${categoryEmoji[c.category]} ${categoryName(c.category)}`;
    emoji.textContent=c.emoji; emoji.hidden=false; image.hidden=true;
    image.onload=()=>{if(requestToken!==state.imageRequest)return;image.hidden=false;emoji.hidden=true;};
    image.onerror=()=>{if(requestToken!==state.imageRequest)return;image.hidden=true;emoji.hidden=false;};
    image.src=openMojiPath(c.emoji);
    $('answer').textContent=c.answer;$('zhuyin').textContent=c.zhuyin;$('zhuyin').hidden=!state.zhuyin;$('hint').textContent=c.hint;
    $('card').classList.remove('changing'); state.locked=false;
  }
  function nextCard(immediate=false){
    if(state.finished)return;
    if(!state.queue.length){finishRound('全部字卡都演完了！');return;}
    state.current=state.queue.shift(); state.locked=true;
    if(immediate) renderCard(); else {$('card').classList.add('changing');later(renderCard,160);}
  }
  function record(result){
    if(state.locked||state.finished||state.screen!=='game')return;
    state.locked=true;
    if(result==='correct'){state.correct.push(state.current);tone('correct');}else{state.skipped.push(state.current);tone('skip');}
    updateScore(); nextCard();
  }
  function finishRound(reason){
    if(state.finished)return;state.finished=true;clearRuntime();tone('end');
    $('correct-total').textContent=state.correct.length;$('skipped-total').textContent=state.skipped.length;
    $('results-title').textContent=state.correct.length>=10?'超級表演王！':state.correct.length>=5?'默契太棒了！':'每一次表演都很精彩！';
    $('result-message').textContent=`${reason} 你們合作完成了 ${state.correct.length+state.skipped.length} 張字卡。`;
    $('result-emoji').textContent=state.correct.length>=10?'🏆':state.correct.length>=5?'🎉':'🌟';
    const list=(title,emoji,items)=>`<section><h3>${emoji} ${title}（${items.length}）</h3>${items.length?`<ul>${items.map(c=>`<li>${c.emoji} ${c.answer}</li>`).join('')}</ul>`:'<p class="empty">這裡還沒有字卡</p>'}</section>`;
    $('history').innerHTML=list('答對','✓',state.correct)+list('跳過','↷',state.skipped);showScreen('results');
  }
  function openEndDialog(){
    if(state.locked||state.finished)return;state.lastFocus=document.activeElement;$('end-dialog').hidden=false;$('confirm-end').focus();
  }
  function closeEndDialog(){ $('end-dialog').hidden=true;if(state.lastFocus)state.lastFocus.focus(); }
  function dialogKeys(event){
    if($('end-dialog').hidden)return;
    if(event.key==='Escape'){event.preventDefault();closeEndDialog();return;}
    if(event.key==='Tab'){const controls=[$('confirm-end'),$('cancel-end')];const i=controls.indexOf(document.activeElement);event.preventDefault();controls[(i+(event.shiftKey?-1:1)+controls.length)%controls.length].focus();}
  }
  document.addEventListener('click',event=>{
    const nav=event.target.closest('[data-nav]');if(nav){const id=nav.dataset.nav;if(state.screen==='game'||state.screen==='countdown')clearRuntime();showScreen(id);}
  });
  $('setup-next').addEventListener('click',beginHandoff);
  $('ready-button').addEventListener('click',prepareRound);
  $('correct-button').addEventListener('click',()=>record('correct'));
  $('skip-button').addEventListener('click',()=>record('skip'));
  $('end-button').addEventListener('click',openEndDialog);
  $('cancel-end').addEventListener('click',closeEndDialog);
  $('confirm-end').addEventListener('click',()=>finishRound('你選擇提早結束。'));
  $('replay-button').addEventListener('click',()=>{showScreen('handoff');$('round-summary').textContent=`${categoryEmoji[state.category]} ${categoryName(state.category)}・${state.duration?state.duration+' 秒':'無限時間'}`;});
  $('sound-toggle').addEventListener('click',()=>{state.sound=!state.sound;savePreference('charades-sound',state.sound);updateToggles();if(state.sound){initAudio();tone('correct');}});
  $('zhuyin-toggle').addEventListener('click',()=>{state.zhuyin=!state.zhuyin;savePreference('charades-zhuyin',state.zhuyin);updateToggles();});

  document.addEventListener('keydown',dialogKeys);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&state.screen==='game')updateTimer();});
  window.addEventListener('pagehide',clearRuntime);
  window.addEventListener('beforeunload',clearRuntime);
  buildCategories();loadPreferences();showScreen('home',false);
  if('serviceWorker' in navigator) window.addEventListener('load',()=>{
    let refreshing=false;
    const hadController=Boolean(navigator.serviceWorker.controller);
    navigator.serviceWorker.addEventListener('controllerchange',()=>{if(hadController&&!refreshing){refreshing=true;location.reload();}});
    navigator.serviceWorker.register('./sw.js').then(registration=>{
      registration.update().catch(()=>{});
      if(registration.waiting) registration.waiting.postMessage({type:'SKIP_WAITING'});
      registration.addEventListener('updatefound',()=>{
        const worker=registration.installing;
        worker&&worker.addEventListener('statechange',()=>{if(worker.state==='installed'&&navigator.serviceWorker.controller)worker.postMessage({type:'SKIP_WAITING'});});
      });
    }).catch(()=>{});
  });
})();
