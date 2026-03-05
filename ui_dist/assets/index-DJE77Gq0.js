(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const l of document.querySelectorAll('link[rel="modulepreload"]'))r(l);new MutationObserver(l=>{for(const c of l)if(c.type==="childList")for(const f of c.addedNodes)f.tagName==="LINK"&&f.rel==="modulepreload"&&r(f)}).observe(document,{childList:!0,subtree:!0});function i(l){const c={};return l.integrity&&(c.integrity=l.integrity),l.referrerPolicy&&(c.referrerPolicy=l.referrerPolicy),l.crossOrigin==="use-credentials"?c.credentials="include":l.crossOrigin==="anonymous"?c.credentials="omit":c.credentials="same-origin",c}function r(l){if(l.ep)return;l.ep=!0;const c=i(l);fetch(l.href,c)}})();var Ch={exports:{}},Xo={};var h0;function HS(){if(h0)return Xo;h0=1;var s=Symbol.for("react.transitional.element"),e=Symbol.for("react.fragment");function i(r,l,c){var f=null;if(c!==void 0&&(f=""+c),l.key!==void 0&&(f=""+l.key),"key"in l){c={};for(var p in l)p!=="key"&&(c[p]=l[p])}else c=l;return l=c.ref,{$$typeof:s,type:r,key:f,ref:l!==void 0?l:null,props:c}}return Xo.Fragment=e,Xo.jsx=i,Xo.jsxs=i,Xo}var d0;function GS(){return d0||(d0=1,Ch.exports=HS()),Ch.exports}var C=GS(),wh={exports:{}},ot={};var p0;function VS(){if(p0)return ot;p0=1;var s=Symbol.for("react.transitional.element"),e=Symbol.for("react.portal"),i=Symbol.for("react.fragment"),r=Symbol.for("react.strict_mode"),l=Symbol.for("react.profiler"),c=Symbol.for("react.consumer"),f=Symbol.for("react.context"),p=Symbol.for("react.forward_ref"),m=Symbol.for("react.suspense"),d=Symbol.for("react.memo"),_=Symbol.for("react.lazy"),v=Symbol.for("react.activity"),g=Symbol.iterator;function M(O){return O===null||typeof O!="object"?null:(O=g&&O[g]||O["@@iterator"],typeof O=="function"?O:null)}var E={isMounted:function(){return!1},enqueueForceUpdate:function(){},enqueueReplaceState:function(){},enqueueSetState:function(){}},R=Object.assign,x={};function y(O,j,ve){this.props=O,this.context=j,this.refs=x,this.updater=ve||E}y.prototype.isReactComponent={},y.prototype.setState=function(O,j){if(typeof O!="object"&&typeof O!="function"&&O!=null)throw Error("takes an object of state variables to update or a function which returns an object of state variables.");this.updater.enqueueSetState(this,O,j,"setState")},y.prototype.forceUpdate=function(O){this.updater.enqueueForceUpdate(this,O,"forceUpdate")};function T(){}T.prototype=y.prototype;function U(O,j,ve){this.props=O,this.context=j,this.refs=x,this.updater=ve||E}var P=U.prototype=new T;P.constructor=U,R(P,y.prototype),P.isPureReactComponent=!0;var V=Array.isArray;function H(){}var z={H:null,A:null,T:null,S:null},A=Object.prototype.hasOwnProperty;function L(O,j,ve){var he=ve.ref;return{$$typeof:s,type:O,key:j,ref:he!==void 0?he:null,props:ve}}function pe(O,j){return L(O.type,j,O.props)}function w(O){return typeof O=="object"&&O!==null&&O.$$typeof===s}function Y(O){var j={"=":"=0",":":"=2"};return"$"+O.replace(/[=:]/g,function(ve){return j[ve]})}var re=/\/+/g;function fe(O,j){return typeof O=="object"&&O!==null&&O.key!=null?Y(""+O.key):j.toString(36)}function ee(O){switch(O.status){case"fulfilled":return O.value;case"rejected":throw O.reason;default:switch(typeof O.status=="string"?O.then(H,H):(O.status="pending",O.then(function(j){O.status==="pending"&&(O.status="fulfilled",O.value=j)},function(j){O.status==="pending"&&(O.status="rejected",O.reason=j)})),O.status){case"fulfilled":return O.value;case"rejected":throw O.reason}}throw O}function I(O,j,ve,he,Ne){var ie=typeof O;(ie==="undefined"||ie==="boolean")&&(O=null);var Se=!1;if(O===null)Se=!0;else switch(ie){case"bigint":case"string":case"number":Se=!0;break;case"object":switch(O.$$typeof){case s:case e:Se=!0;break;case _:return Se=O._init,I(Se(O._payload),j,ve,he,Ne)}}if(Se)return Ne=Ne(O),Se=he===""?"."+fe(O,0):he,V(Ne)?(ve="",Se!=null&&(ve=Se.replace(re,"$&/")+"/"),I(Ne,j,ve,"",function(Qe){return Qe})):Ne!=null&&(w(Ne)&&(Ne=pe(Ne,ve+(Ne.key==null||O&&O.key===Ne.key?"":(""+Ne.key).replace(re,"$&/")+"/")+Se)),j.push(Ne)),1;Se=0;var Ae=he===""?".":he+":";if(V(O))for(var Ge=0;Ge<O.length;Ge++)he=O[Ge],ie=Ae+fe(he,Ge),Se+=I(he,j,ve,ie,Ne);else if(Ge=M(O),typeof Ge=="function")for(O=Ge.call(O),Ge=0;!(he=O.next()).done;)he=he.value,ie=Ae+fe(he,Ge++),Se+=I(he,j,ve,ie,Ne);else if(ie==="object"){if(typeof O.then=="function")return I(ee(O),j,ve,he,Ne);throw j=String(O),Error("Objects are not valid as a React child (found: "+(j==="[object Object]"?"object with keys {"+Object.keys(O).join(", ")+"}":j)+"). If you meant to render a collection of children, use an array instead.")}return Se}function B(O,j,ve){if(O==null)return O;var he=[],Ne=0;return I(O,he,"","",function(ie){return j.call(ve,ie,Ne++)}),he}function $(O){if(O._status===-1){var j=O._result;j=j(),j.then(function(ve){(O._status===0||O._status===-1)&&(O._status=1,O._result=ve)},function(ve){(O._status===0||O._status===-1)&&(O._status=2,O._result=ve)}),O._status===-1&&(O._status=0,O._result=j)}if(O._status===1)return O._result.default;throw O._result}var Q=typeof reportError=="function"?reportError:function(O){if(typeof window=="object"&&typeof window.ErrorEvent=="function"){var j=new window.ErrorEvent("error",{bubbles:!0,cancelable:!0,message:typeof O=="object"&&O!==null&&typeof O.message=="string"?String(O.message):String(O),error:O});if(!window.dispatchEvent(j))return}else if(typeof process=="object"&&typeof process.emit=="function"){process.emit("uncaughtException",O);return}console.error(O)},de={map:B,forEach:function(O,j,ve){B(O,function(){j.apply(this,arguments)},ve)},count:function(O){var j=0;return B(O,function(){j++}),j},toArray:function(O){return B(O,function(j){return j})||[]},only:function(O){if(!w(O))throw Error("React.Children.only expected to receive a single React element child.");return O}};return ot.Activity=v,ot.Children=de,ot.Component=y,ot.Fragment=i,ot.Profiler=l,ot.PureComponent=U,ot.StrictMode=r,ot.Suspense=m,ot.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE=z,ot.__COMPILER_RUNTIME={__proto__:null,c:function(O){return z.H.useMemoCache(O)}},ot.cache=function(O){return function(){return O.apply(null,arguments)}},ot.cacheSignal=function(){return null},ot.cloneElement=function(O,j,ve){if(O==null)throw Error("The argument must be a React element, but you passed "+O+".");var he=R({},O.props),Ne=O.key;if(j!=null)for(ie in j.key!==void 0&&(Ne=""+j.key),j)!A.call(j,ie)||ie==="key"||ie==="__self"||ie==="__source"||ie==="ref"&&j.ref===void 0||(he[ie]=j[ie]);var ie=arguments.length-2;if(ie===1)he.children=ve;else if(1<ie){for(var Se=Array(ie),Ae=0;Ae<ie;Ae++)Se[Ae]=arguments[Ae+2];he.children=Se}return L(O.type,Ne,he)},ot.createContext=function(O){return O={$$typeof:f,_currentValue:O,_currentValue2:O,_threadCount:0,Provider:null,Consumer:null},O.Provider=O,O.Consumer={$$typeof:c,_context:O},O},ot.createElement=function(O,j,ve){var he,Ne={},ie=null;if(j!=null)for(he in j.key!==void 0&&(ie=""+j.key),j)A.call(j,he)&&he!=="key"&&he!=="__self"&&he!=="__source"&&(Ne[he]=j[he]);var Se=arguments.length-2;if(Se===1)Ne.children=ve;else if(1<Se){for(var Ae=Array(Se),Ge=0;Ge<Se;Ge++)Ae[Ge]=arguments[Ge+2];Ne.children=Ae}if(O&&O.defaultProps)for(he in Se=O.defaultProps,Se)Ne[he]===void 0&&(Ne[he]=Se[he]);return L(O,ie,Ne)},ot.createRef=function(){return{current:null}},ot.forwardRef=function(O){return{$$typeof:p,render:O}},ot.isValidElement=w,ot.lazy=function(O){return{$$typeof:_,_payload:{_status:-1,_result:O},_init:$}},ot.memo=function(O,j){return{$$typeof:d,type:O,compare:j===void 0?null:j}},ot.startTransition=function(O){var j=z.T,ve={};z.T=ve;try{var he=O(),Ne=z.S;Ne!==null&&Ne(ve,he),typeof he=="object"&&he!==null&&typeof he.then=="function"&&he.then(H,Q)}catch(ie){Q(ie)}finally{j!==null&&ve.types!==null&&(j.types=ve.types),z.T=j}},ot.unstable_useCacheRefresh=function(){return z.H.useCacheRefresh()},ot.use=function(O){return z.H.use(O)},ot.useActionState=function(O,j,ve){return z.H.useActionState(O,j,ve)},ot.useCallback=function(O,j){return z.H.useCallback(O,j)},ot.useContext=function(O){return z.H.useContext(O)},ot.useDebugValue=function(){},ot.useDeferredValue=function(O,j){return z.H.useDeferredValue(O,j)},ot.useEffect=function(O,j){return z.H.useEffect(O,j)},ot.useEffectEvent=function(O){return z.H.useEffectEvent(O)},ot.useId=function(){return z.H.useId()},ot.useImperativeHandle=function(O,j,ve){return z.H.useImperativeHandle(O,j,ve)},ot.useInsertionEffect=function(O,j){return z.H.useInsertionEffect(O,j)},ot.useLayoutEffect=function(O,j){return z.H.useLayoutEffect(O,j)},ot.useMemo=function(O,j){return z.H.useMemo(O,j)},ot.useOptimistic=function(O,j){return z.H.useOptimistic(O,j)},ot.useReducer=function(O,j,ve){return z.H.useReducer(O,j,ve)},ot.useRef=function(O){return z.H.useRef(O)},ot.useState=function(O){return z.H.useState(O)},ot.useSyncExternalStore=function(O,j,ve){return z.H.useSyncExternalStore(O,j,ve)},ot.useTransition=function(){return z.H.useTransition()},ot.version="19.2.4",ot}var m0;function dp(){return m0||(m0=1,wh.exports=VS()),wh.exports}var K=dp(),Dh={exports:{}},Wo={},Nh={exports:{}},Uh={};var g0;function kS(){return g0||(g0=1,(function(s){function e(I,B){var $=I.length;I.push(B);e:for(;0<$;){var Q=$-1>>>1,de=I[Q];if(0<l(de,B))I[Q]=B,I[$]=de,$=Q;else break e}}function i(I){return I.length===0?null:I[0]}function r(I){if(I.length===0)return null;var B=I[0],$=I.pop();if($!==B){I[0]=$;e:for(var Q=0,de=I.length,O=de>>>1;Q<O;){var j=2*(Q+1)-1,ve=I[j],he=j+1,Ne=I[he];if(0>l(ve,$))he<de&&0>l(Ne,ve)?(I[Q]=Ne,I[he]=$,Q=he):(I[Q]=ve,I[j]=$,Q=j);else if(he<de&&0>l(Ne,$))I[Q]=Ne,I[he]=$,Q=he;else break e}}return B}function l(I,B){var $=I.sortIndex-B.sortIndex;return $!==0?$:I.id-B.id}if(s.unstable_now=void 0,typeof performance=="object"&&typeof performance.now=="function"){var c=performance;s.unstable_now=function(){return c.now()}}else{var f=Date,p=f.now();s.unstable_now=function(){return f.now()-p}}var m=[],d=[],_=1,v=null,g=3,M=!1,E=!1,R=!1,x=!1,y=typeof setTimeout=="function"?setTimeout:null,T=typeof clearTimeout=="function"?clearTimeout:null,U=typeof setImmediate<"u"?setImmediate:null;function P(I){for(var B=i(d);B!==null;){if(B.callback===null)r(d);else if(B.startTime<=I)r(d),B.sortIndex=B.expirationTime,e(m,B);else break;B=i(d)}}function V(I){if(R=!1,P(I),!E)if(i(m)!==null)E=!0,H||(H=!0,Y());else{var B=i(d);B!==null&&ee(V,B.startTime-I)}}var H=!1,z=-1,A=5,L=-1;function pe(){return x?!0:!(s.unstable_now()-L<A)}function w(){if(x=!1,H){var I=s.unstable_now();L=I;var B=!0;try{e:{E=!1,R&&(R=!1,T(z),z=-1),M=!0;var $=g;try{t:{for(P(I),v=i(m);v!==null&&!(v.expirationTime>I&&pe());){var Q=v.callback;if(typeof Q=="function"){v.callback=null,g=v.priorityLevel;var de=Q(v.expirationTime<=I);if(I=s.unstable_now(),typeof de=="function"){v.callback=de,P(I),B=!0;break t}v===i(m)&&r(m),P(I)}else r(m);v=i(m)}if(v!==null)B=!0;else{var O=i(d);O!==null&&ee(V,O.startTime-I),B=!1}}break e}finally{v=null,g=$,M=!1}B=void 0}}finally{B?Y():H=!1}}}var Y;if(typeof U=="function")Y=function(){U(w)};else if(typeof MessageChannel<"u"){var re=new MessageChannel,fe=re.port2;re.port1.onmessage=w,Y=function(){fe.postMessage(null)}}else Y=function(){y(w,0)};function ee(I,B){z=y(function(){I(s.unstable_now())},B)}s.unstable_IdlePriority=5,s.unstable_ImmediatePriority=1,s.unstable_LowPriority=4,s.unstable_NormalPriority=3,s.unstable_Profiling=null,s.unstable_UserBlockingPriority=2,s.unstable_cancelCallback=function(I){I.callback=null},s.unstable_forceFrameRate=function(I){0>I||125<I?console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported"):A=0<I?Math.floor(1e3/I):5},s.unstable_getCurrentPriorityLevel=function(){return g},s.unstable_next=function(I){switch(g){case 1:case 2:case 3:var B=3;break;default:B=g}var $=g;g=B;try{return I()}finally{g=$}},s.unstable_requestPaint=function(){x=!0},s.unstable_runWithPriority=function(I,B){switch(I){case 1:case 2:case 3:case 4:case 5:break;default:I=3}var $=g;g=I;try{return B()}finally{g=$}},s.unstable_scheduleCallback=function(I,B,$){var Q=s.unstable_now();switch(typeof $=="object"&&$!==null?($=$.delay,$=typeof $=="number"&&0<$?Q+$:Q):$=Q,I){case 1:var de=-1;break;case 2:de=250;break;case 5:de=1073741823;break;case 4:de=1e4;break;default:de=5e3}return de=$+de,I={id:_++,callback:B,priorityLevel:I,startTime:$,expirationTime:de,sortIndex:-1},$>Q?(I.sortIndex=$,e(d,I),i(m)===null&&I===i(d)&&(R?(T(z),z=-1):R=!0,ee(V,$-Q))):(I.sortIndex=de,e(m,I),E||M||(E=!0,H||(H=!0,Y()))),I},s.unstable_shouldYield=pe,s.unstable_wrapCallback=function(I){var B=g;return function(){var $=g;g=B;try{return I.apply(this,arguments)}finally{g=$}}}})(Uh)),Uh}var _0;function jS(){return _0||(_0=1,Nh.exports=kS()),Nh.exports}var Lh={exports:{}},Cn={};var v0;function XS(){if(v0)return Cn;v0=1;var s=dp();function e(m){var d="https://react.dev/errors/"+m;if(1<arguments.length){d+="?args[]="+encodeURIComponent(arguments[1]);for(var _=2;_<arguments.length;_++)d+="&args[]="+encodeURIComponent(arguments[_])}return"Minified React error #"+m+"; visit "+d+" for the full message or use the non-minified dev environment for full errors and additional helpful warnings."}function i(){}var r={d:{f:i,r:function(){throw Error(e(522))},D:i,C:i,L:i,m:i,X:i,S:i,M:i},p:0,findDOMNode:null},l=Symbol.for("react.portal");function c(m,d,_){var v=3<arguments.length&&arguments[3]!==void 0?arguments[3]:null;return{$$typeof:l,key:v==null?null:""+v,children:m,containerInfo:d,implementation:_}}var f=s.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;function p(m,d){if(m==="font")return"";if(typeof d=="string")return d==="use-credentials"?d:""}return Cn.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE=r,Cn.createPortal=function(m,d){var _=2<arguments.length&&arguments[2]!==void 0?arguments[2]:null;if(!d||d.nodeType!==1&&d.nodeType!==9&&d.nodeType!==11)throw Error(e(299));return c(m,d,null,_)},Cn.flushSync=function(m){var d=f.T,_=r.p;try{if(f.T=null,r.p=2,m)return m()}finally{f.T=d,r.p=_,r.d.f()}},Cn.preconnect=function(m,d){typeof m=="string"&&(d?(d=d.crossOrigin,d=typeof d=="string"?d==="use-credentials"?d:"":void 0):d=null,r.d.C(m,d))},Cn.prefetchDNS=function(m){typeof m=="string"&&r.d.D(m)},Cn.preinit=function(m,d){if(typeof m=="string"&&d&&typeof d.as=="string"){var _=d.as,v=p(_,d.crossOrigin),g=typeof d.integrity=="string"?d.integrity:void 0,M=typeof d.fetchPriority=="string"?d.fetchPriority:void 0;_==="style"?r.d.S(m,typeof d.precedence=="string"?d.precedence:void 0,{crossOrigin:v,integrity:g,fetchPriority:M}):_==="script"&&r.d.X(m,{crossOrigin:v,integrity:g,fetchPriority:M,nonce:typeof d.nonce=="string"?d.nonce:void 0})}},Cn.preinitModule=function(m,d){if(typeof m=="string")if(typeof d=="object"&&d!==null){if(d.as==null||d.as==="script"){var _=p(d.as,d.crossOrigin);r.d.M(m,{crossOrigin:_,integrity:typeof d.integrity=="string"?d.integrity:void 0,nonce:typeof d.nonce=="string"?d.nonce:void 0})}}else d==null&&r.d.M(m)},Cn.preload=function(m,d){if(typeof m=="string"&&typeof d=="object"&&d!==null&&typeof d.as=="string"){var _=d.as,v=p(_,d.crossOrigin);r.d.L(m,_,{crossOrigin:v,integrity:typeof d.integrity=="string"?d.integrity:void 0,nonce:typeof d.nonce=="string"?d.nonce:void 0,type:typeof d.type=="string"?d.type:void 0,fetchPriority:typeof d.fetchPriority=="string"?d.fetchPriority:void 0,referrerPolicy:typeof d.referrerPolicy=="string"?d.referrerPolicy:void 0,imageSrcSet:typeof d.imageSrcSet=="string"?d.imageSrcSet:void 0,imageSizes:typeof d.imageSizes=="string"?d.imageSizes:void 0,media:typeof d.media=="string"?d.media:void 0})}},Cn.preloadModule=function(m,d){if(typeof m=="string")if(d){var _=p(d.as,d.crossOrigin);r.d.m(m,{as:typeof d.as=="string"&&d.as!=="script"?d.as:void 0,crossOrigin:_,integrity:typeof d.integrity=="string"?d.integrity:void 0})}else r.d.m(m)},Cn.requestFormReset=function(m){r.d.r(m)},Cn.unstable_batchedUpdates=function(m,d){return m(d)},Cn.useFormState=function(m,d,_){return f.H.useFormState(m,d,_)},Cn.useFormStatus=function(){return f.H.useHostTransitionStatus()},Cn.version="19.2.4",Cn}var x0;function WS(){if(x0)return Lh.exports;x0=1;function s(){if(!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__>"u"||typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE!="function"))try{__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(s)}catch(e){console.error(e)}}return s(),Lh.exports=XS(),Lh.exports}var y0;function qS(){if(y0)return Wo;y0=1;var s=jS(),e=dp(),i=WS();function r(t){var n="https://react.dev/errors/"+t;if(1<arguments.length){n+="?args[]="+encodeURIComponent(arguments[1]);for(var a=2;a<arguments.length;a++)n+="&args[]="+encodeURIComponent(arguments[a])}return"Minified React error #"+t+"; visit "+n+" for the full message or use the non-minified dev environment for full errors and additional helpful warnings."}function l(t){return!(!t||t.nodeType!==1&&t.nodeType!==9&&t.nodeType!==11)}function c(t){var n=t,a=t;if(t.alternate)for(;n.return;)n=n.return;else{t=n;do n=t,(n.flags&4098)!==0&&(a=n.return),t=n.return;while(t)}return n.tag===3?a:null}function f(t){if(t.tag===13){var n=t.memoizedState;if(n===null&&(t=t.alternate,t!==null&&(n=t.memoizedState)),n!==null)return n.dehydrated}return null}function p(t){if(t.tag===31){var n=t.memoizedState;if(n===null&&(t=t.alternate,t!==null&&(n=t.memoizedState)),n!==null)return n.dehydrated}return null}function m(t){if(c(t)!==t)throw Error(r(188))}function d(t){var n=t.alternate;if(!n){if(n=c(t),n===null)throw Error(r(188));return n!==t?null:t}for(var a=t,o=n;;){var u=a.return;if(u===null)break;var h=u.alternate;if(h===null){if(o=u.return,o!==null){a=o;continue}break}if(u.child===h.child){for(h=u.child;h;){if(h===a)return m(u),t;if(h===o)return m(u),n;h=h.sibling}throw Error(r(188))}if(a.return!==o.return)a=u,o=h;else{for(var S=!1,D=u.child;D;){if(D===a){S=!0,a=u,o=h;break}if(D===o){S=!0,o=u,a=h;break}D=D.sibling}if(!S){for(D=h.child;D;){if(D===a){S=!0,a=h,o=u;break}if(D===o){S=!0,o=h,a=u;break}D=D.sibling}if(!S)throw Error(r(189))}}if(a.alternate!==o)throw Error(r(190))}if(a.tag!==3)throw Error(r(188));return a.stateNode.current===a?t:n}function _(t){var n=t.tag;if(n===5||n===26||n===27||n===6)return t;for(t=t.child;t!==null;){if(n=_(t),n!==null)return n;t=t.sibling}return null}var v=Object.assign,g=Symbol.for("react.element"),M=Symbol.for("react.transitional.element"),E=Symbol.for("react.portal"),R=Symbol.for("react.fragment"),x=Symbol.for("react.strict_mode"),y=Symbol.for("react.profiler"),T=Symbol.for("react.consumer"),U=Symbol.for("react.context"),P=Symbol.for("react.forward_ref"),V=Symbol.for("react.suspense"),H=Symbol.for("react.suspense_list"),z=Symbol.for("react.memo"),A=Symbol.for("react.lazy"),L=Symbol.for("react.activity"),pe=Symbol.for("react.memo_cache_sentinel"),w=Symbol.iterator;function Y(t){return t===null||typeof t!="object"?null:(t=w&&t[w]||t["@@iterator"],typeof t=="function"?t:null)}var re=Symbol.for("react.client.reference");function fe(t){if(t==null)return null;if(typeof t=="function")return t.$$typeof===re?null:t.displayName||t.name||null;if(typeof t=="string")return t;switch(t){case R:return"Fragment";case y:return"Profiler";case x:return"StrictMode";case V:return"Suspense";case H:return"SuspenseList";case L:return"Activity"}if(typeof t=="object")switch(t.$$typeof){case E:return"Portal";case U:return t.displayName||"Context";case T:return(t._context.displayName||"Context")+".Consumer";case P:var n=t.render;return t=t.displayName,t||(t=n.displayName||n.name||"",t=t!==""?"ForwardRef("+t+")":"ForwardRef"),t;case z:return n=t.displayName||null,n!==null?n:fe(t.type)||"Memo";case A:n=t._payload,t=t._init;try{return fe(t(n))}catch{}}return null}var ee=Array.isArray,I=e.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE,B=i.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE,$={pending:!1,data:null,method:null,action:null},Q=[],de=-1;function O(t){return{current:t}}function j(t){0>de||(t.current=Q[de],Q[de]=null,de--)}function ve(t,n){de++,Q[de]=t.current,t.current=n}var he=O(null),Ne=O(null),ie=O(null),Se=O(null);function Ae(t,n){switch(ve(ie,n),ve(Ne,t),ve(he,null),n.nodeType){case 9:case 11:t=(t=n.documentElement)&&(t=t.namespaceURI)?P_(t):0;break;default:if(t=n.tagName,n=n.namespaceURI)n=P_(n),t=F_(n,t);else switch(t){case"svg":t=1;break;case"math":t=2;break;default:t=0}}j(he),ve(he,t)}function Ge(){j(he),j(Ne),j(ie)}function Qe(t){t.memoizedState!==null&&ve(Se,t);var n=he.current,a=F_(n,t.type);n!==a&&(ve(Ne,t),ve(he,a))}function qe(t){Ne.current===t&&(j(he),j(Ne)),Se.current===t&&(j(Se),Go._currentValue=$)}var $t,yt;function gt(t){if($t===void 0)try{throw Error()}catch(a){var n=a.stack.trim().match(/\n( *(at )?)/);$t=n&&n[1]||"",yt=-1<a.stack.indexOf(`
    at`)?" (<anonymous>)":-1<a.stack.indexOf("@")?"@unknown:0:0":""}return`
`+$t+t+yt}var Nt=!1;function lt(t,n){if(!t||Nt)return"";Nt=!0;var a=Error.prepareStackTrace;Error.prepareStackTrace=void 0;try{var o={DetermineComponentFrameRoot:function(){try{if(n){var Me=function(){throw Error()};if(Object.defineProperty(Me.prototype,"props",{set:function(){throw Error()}}),typeof Reflect=="object"&&Reflect.construct){try{Reflect.construct(Me,[])}catch(ue){var le=ue}Reflect.construct(t,[],Me)}else{try{Me.call()}catch(ue){le=ue}t.call(Me.prototype)}}else{try{throw Error()}catch(ue){le=ue}(Me=t())&&typeof Me.catch=="function"&&Me.catch(function(){})}}catch(ue){if(ue&&le&&typeof ue.stack=="string")return[ue.stack,le.stack]}return[null,null]}};o.DetermineComponentFrameRoot.displayName="DetermineComponentFrameRoot";var u=Object.getOwnPropertyDescriptor(o.DetermineComponentFrameRoot,"name");u&&u.configurable&&Object.defineProperty(o.DetermineComponentFrameRoot,"name",{value:"DetermineComponentFrameRoot"});var h=o.DetermineComponentFrameRoot(),S=h[0],D=h[1];if(S&&D){var G=S.split(`
`),ae=D.split(`
`);for(u=o=0;o<G.length&&!G[o].includes("DetermineComponentFrameRoot");)o++;for(;u<ae.length&&!ae[u].includes("DetermineComponentFrameRoot");)u++;if(o===G.length||u===ae.length)for(o=G.length-1,u=ae.length-1;1<=o&&0<=u&&G[o]!==ae[u];)u--;for(;1<=o&&0<=u;o--,u--)if(G[o]!==ae[u]){if(o!==1||u!==1)do if(o--,u--,0>u||G[o]!==ae[u]){var _e=`
`+G[o].replace(" at new "," at ");return t.displayName&&_e.includes("<anonymous>")&&(_e=_e.replace("<anonymous>",t.displayName)),_e}while(1<=o&&0<=u);break}}}finally{Nt=!1,Error.prepareStackTrace=a}return(a=t?t.displayName||t.name:"")?gt(a):""}function Jt(t,n){switch(t.tag){case 26:case 27:case 5:return gt(t.type);case 16:return gt("Lazy");case 13:return t.child!==n&&n!==null?gt("Suspense Fallback"):gt("Suspense");case 19:return gt("SuspenseList");case 0:case 15:return lt(t.type,!1);case 11:return lt(t.type.render,!1);case 1:return lt(t.type,!0);case 31:return gt("Activity");default:return""}}function k(t){try{var n="",a=null;do n+=Jt(t,a),a=t,t=t.return;while(t);return n}catch(o){return`
Error generating stack: `+o.message+`
`+o.stack}}var qt=Object.prototype.hasOwnProperty,bt=s.unstable_scheduleCallback,Ot=s.unstable_cancelCallback,Ye=s.unstable_shouldYield,F=s.unstable_requestPaint,b=s.unstable_now,Z=s.unstable_getCurrentPriorityLevel,xe=s.unstable_ImmediatePriority,Ee=s.unstable_UserBlockingPriority,ge=s.unstable_NormalPriority,Xe=s.unstable_LowPriority,De=s.unstable_IdlePriority,Je=s.log,tt=s.unstable_setDisableYieldValue,Re=null,be=null;function Fe(t){if(typeof Je=="function"&&tt(t),be&&typeof be.setStrictMode=="function")try{be.setStrictMode(Re,t)}catch{}}var Pe=Math.clz32?Math.clz32:q,Ie=Math.log,ut=Math.LN2;function q(t){return t>>>=0,t===0?32:31-(Ie(t)/ut|0)|0}var we=256,Ce=262144,ze=4194304;function Te(t){var n=t&42;if(n!==0)return n;switch(t&-t){case 1:return 1;case 2:return 2;case 4:return 4;case 8:return 8;case 16:return 16;case 32:return 32;case 64:return 64;case 128:return 128;case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:return t&261888;case 262144:case 524288:case 1048576:case 2097152:return t&3932160;case 4194304:case 8388608:case 16777216:case 33554432:return t&62914560;case 67108864:return 67108864;case 134217728:return 134217728;case 268435456:return 268435456;case 536870912:return 536870912;case 1073741824:return 0;default:return t}}function me(t,n,a){var o=t.pendingLanes;if(o===0)return 0;var u=0,h=t.suspendedLanes,S=t.pingedLanes;t=t.warmLanes;var D=o&134217727;return D!==0?(o=D&~h,o!==0?u=Te(o):(S&=D,S!==0?u=Te(S):a||(a=D&~t,a!==0&&(u=Te(a))))):(D=o&~h,D!==0?u=Te(D):S!==0?u=Te(S):a||(a=o&~t,a!==0&&(u=Te(a)))),u===0?0:n!==0&&n!==u&&(n&h)===0&&(h=u&-u,a=n&-n,h>=a||h===32&&(a&4194048)!==0)?n:u}function He(t,n){return(t.pendingLanes&~(t.suspendedLanes&~t.pingedLanes)&n)===0}function it(t,n){switch(t){case 1:case 2:case 4:case 8:case 64:return n+250;case 16:case 32:case 128:case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:return n+5e3;case 4194304:case 8388608:case 16777216:case 33554432:return-1;case 67108864:case 134217728:case 268435456:case 536870912:case 1073741824:return-1;default:return-1}}function Ft(){var t=ze;return ze<<=1,(ze&62914560)===0&&(ze=4194304),t}function Tt(t){for(var n=[],a=0;31>a;a++)n.push(t);return n}function Ln(t,n){t.pendingLanes|=n,n!==268435456&&(t.suspendedLanes=0,t.pingedLanes=0,t.warmLanes=0)}function Mi(t,n,a,o,u,h){var S=t.pendingLanes;t.pendingLanes=a,t.suspendedLanes=0,t.pingedLanes=0,t.warmLanes=0,t.expiredLanes&=a,t.entangledLanes&=a,t.errorRecoveryDisabledLanes&=a,t.shellSuspendCounter=0;var D=t.entanglements,G=t.expirationTimes,ae=t.hiddenUpdates;for(a=S&~a;0<a;){var _e=31-Pe(a),Me=1<<_e;D[_e]=0,G[_e]=-1;var le=ae[_e];if(le!==null)for(ae[_e]=null,_e=0;_e<le.length;_e++){var ue=le[_e];ue!==null&&(ue.lane&=-536870913)}a&=~Me}o!==0&&to(t,o,0),h!==0&&u===0&&t.tag!==0&&(t.suspendedLanes|=h&~(S&~n))}function to(t,n,a){t.pendingLanes|=n,t.suspendedLanes&=~n;var o=31-Pe(n);t.entangledLanes|=n,t.entanglements[o]=t.entanglements[o]|1073741824|a&261930}function Ws(t,n){var a=t.entangledLanes|=n;for(t=t.entanglements;a;){var o=31-Pe(a),u=1<<o;u&n|t[o]&n&&(t[o]|=n),a&=~u}}function gl(t,n){var a=n&-n;return a=(a&42)!==0?1:qs(a),(a&(t.suspendedLanes|n))!==0?0:a}function qs(t){switch(t){case 2:t=1;break;case 8:t=4;break;case 32:t=16;break;case 256:case 512:case 1024:case 2048:case 4096:case 8192:case 16384:case 32768:case 65536:case 131072:case 262144:case 524288:case 1048576:case 2097152:case 4194304:case 8388608:case 16777216:case 33554432:t=128;break;case 268435456:t=134217728;break;default:t=0}return t}function Ys(t){return t&=-t,2<t?8<t?(t&134217727)!==0?32:268435456:8:2}function Ii(){var t=B.p;return t!==0?t:(t=window.event,t===void 0?32:s0(t.type))}function Zs(t,n){var a=B.p;try{return B.p=t,n()}finally{B.p=a}}var Ei=Math.random().toString(36).slice(2),on="__reactFiber$"+Ei,mn="__reactProps$"+Ei,Qi="__reactContainer$"+Ei,Ua="__reactEvents$"+Ei,_l="__reactListeners$"+Ei,vl="__reactHandles$"+Ei,xl="__reactResources$"+Ei,gs="__reactMarker$"+Ei;function no(t){delete t[on],delete t[mn],delete t[Ua],delete t[_l],delete t[vl]}function La(t){var n=t[on];if(n)return n;for(var a=t.parentNode;a;){if(n=a[Qi]||a[on]){if(a=n.alternate,n.child!==null||a!==null&&a.child!==null)for(t=k_(t);t!==null;){if(a=t[on])return a;t=k_(t)}return n}t=a,a=t.parentNode}return null}function Oa(t){if(t=t[on]||t[Qi]){var n=t.tag;if(n===5||n===6||n===13||n===31||n===26||n===27||n===3)return t}return null}function _s(t){var n=t.tag;if(n===5||n===26||n===27||n===6)return t.stateNode;throw Error(r(33))}function N(t){var n=t[xl];return n||(n=t[xl]={hoistableStyles:new Map,hoistableScripts:new Map}),n}function W(t){t[gs]=!0}var ce=new Set,oe={};function te(t,n){Ue(t,n),Ue(t+"Capture",n)}function Ue(t,n){for(oe[t]=n,t=0;t<n.length;t++)ce.add(n[t])}var Be=RegExp("^[:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD][:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD\\-.0-9\\u00B7\\u0300-\\u036F\\u203F-\\u2040]*$"),Le={},We={};function Ke(t){return qt.call(We,t)?!0:qt.call(Le,t)?!1:Be.test(t)?We[t]=!0:(Le[t]=!0,!1)}function nt(t,n,a){if(Ke(n))if(a===null)t.removeAttribute(n);else{switch(typeof a){case"undefined":case"function":case"symbol":t.removeAttribute(n);return;case"boolean":var o=n.toLowerCase().slice(0,5);if(o!=="data-"&&o!=="aria-"){t.removeAttribute(n);return}}t.setAttribute(n,""+a)}}function rt(t,n,a){if(a===null)t.removeAttribute(n);else{switch(typeof a){case"undefined":case"function":case"symbol":case"boolean":t.removeAttribute(n);return}t.setAttribute(n,""+a)}}function Ve(t,n,a,o){if(o===null)t.removeAttribute(a);else{switch(typeof o){case"undefined":case"function":case"symbol":case"boolean":t.removeAttribute(a);return}t.setAttributeNS(n,a,""+o)}}function ft(t){switch(typeof t){case"bigint":case"boolean":case"number":case"string":case"undefined":return t;case"object":return t;default:return""}}function Yt(t){var n=t.type;return(t=t.nodeName)&&t.toLowerCase()==="input"&&(n==="checkbox"||n==="radio")}function Zt(t,n,a){var o=Object.getOwnPropertyDescriptor(t.constructor.prototype,n);if(!t.hasOwnProperty(n)&&typeof o<"u"&&typeof o.get=="function"&&typeof o.set=="function"){var u=o.get,h=o.set;return Object.defineProperty(t,n,{configurable:!0,get:function(){return u.call(this)},set:function(S){a=""+S,h.call(this,S)}}),Object.defineProperty(t,n,{enumerable:o.enumerable}),{getValue:function(){return a},setValue:function(S){a=""+S},stopTracking:function(){t._valueTracker=null,delete t[n]}}}}function Ct(t){if(!t._valueTracker){var n=Yt(t)?"checked":"value";t._valueTracker=Zt(t,n,""+t[n])}}function gn(t){if(!t)return!1;var n=t._valueTracker;if(!n)return!0;var a=n.getValue(),o="";return t&&(o=Yt(t)?t.checked?"true":"false":t.value),t=o,t!==a?(n.setValue(t),!0):!1}function je(t){if(t=t||(typeof document<"u"?document:void 0),typeof t>"u")return null;try{return t.activeElement||t.body}catch{return t.body}}var On=/[\n"\\]/g;function at(t){return t.replace(On,function(n){return"\\"+n.charCodeAt(0).toString(16)+" "})}function Pn(t,n,a,o,u,h,S,D){t.name="",S!=null&&typeof S!="function"&&typeof S!="symbol"&&typeof S!="boolean"?t.type=S:t.removeAttribute("type"),n!=null?S==="number"?(n===0&&t.value===""||t.value!=n)&&(t.value=""+ft(n)):t.value!==""+ft(n)&&(t.value=""+ft(n)):S!=="submit"&&S!=="reset"||t.removeAttribute("value"),n!=null?bi(t,S,ft(n)):a!=null?bi(t,S,ft(a)):o!=null&&t.removeAttribute("value"),u==null&&h!=null&&(t.defaultChecked=!!h),u!=null&&(t.checked=u&&typeof u!="function"&&typeof u!="symbol"),D!=null&&typeof D!="function"&&typeof D!="symbol"&&typeof D!="boolean"?t.name=""+ft(D):t.removeAttribute("name")}function Qn(t,n,a,o,u,h,S,D){if(h!=null&&typeof h!="function"&&typeof h!="symbol"&&typeof h!="boolean"&&(t.type=h),n!=null||a!=null){if(!(h!=="submit"&&h!=="reset"||n!=null)){Ct(t);return}a=a!=null?""+ft(a):"",n=n!=null?""+ft(n):a,D||n===t.value||(t.value=n),t.defaultValue=n}o=o??u,o=typeof o!="function"&&typeof o!="symbol"&&!!o,t.checked=D?t.checked:!!o,t.defaultChecked=!!o,S!=null&&typeof S!="function"&&typeof S!="symbol"&&typeof S!="boolean"&&(t.name=S),Ct(t)}function bi(t,n,a){n==="number"&&je(t.ownerDocument)===t||t.defaultValue===""+a||(t.defaultValue=""+a)}function Jn(t,n,a,o){if(t=t.options,n){n={};for(var u=0;u<a.length;u++)n["$"+a[u]]=!0;for(a=0;a<t.length;a++)u=n.hasOwnProperty("$"+t[a].value),t[a].selected!==u&&(t[a].selected=u),u&&o&&(t[a].defaultSelected=!0)}else{for(a=""+ft(a),n=null,u=0;u<t.length;u++){if(t[u].value===a){t[u].selected=!0,o&&(t[u].defaultSelected=!0);return}n!==null||t[u].disabled||(n=t[u])}n!==null&&(n.selected=!0)}}function Pt(t,n,a){if(n!=null&&(n=""+ft(n),n!==t.value&&(t.value=n),a==null)){t.defaultValue!==n&&(t.defaultValue=n);return}t.defaultValue=a!=null?""+ft(a):""}function ln(t,n,a,o){if(n==null){if(o!=null){if(a!=null)throw Error(r(92));if(ee(o)){if(1<o.length)throw Error(r(93));o=o[0]}a=o}a==null&&(a=""),n=a}a=ft(n),t.defaultValue=a,o=t.textContent,o===a&&o!==""&&o!==null&&(t.value=o),Ct(t)}function Fn(t,n){if(n){var a=t.firstChild;if(a&&a===t.lastChild&&a.nodeType===3){a.nodeValue=n;return}}t.textContent=n}var cn=new Set("animationIterationCount aspectRatio borderImageOutset borderImageSlice borderImageWidth boxFlex boxFlexGroup boxOrdinalGroup columnCount columns flex flexGrow flexPositive flexShrink flexNegative flexOrder gridArea gridRow gridRowEnd gridRowSpan gridRowStart gridColumn gridColumnEnd gridColumnSpan gridColumnStart fontWeight lineClamp lineHeight opacity order orphans scale tabSize widows zIndex zoom fillOpacity floodOpacity stopOpacity strokeDasharray strokeDashoffset strokeMiterlimit strokeOpacity strokeWidth MozAnimationIterationCount MozBoxFlex MozBoxFlexGroup MozLineClamp msAnimationIterationCount msFlex msZoom msFlexGrow msFlexNegative msFlexOrder msFlexPositive msFlexShrink msGridColumn msGridColumnSpan msGridRow msGridRowSpan WebkitAnimationIterationCount WebkitBoxFlex WebKitBoxFlexGroup WebkitBoxOrdinalGroup WebkitColumnCount WebkitColumns WebkitFlex WebkitFlexGrow WebkitFlexPositive WebkitFlexShrink WebkitLineClamp".split(" "));function Ti(t,n,a){var o=n.indexOf("--")===0;a==null||typeof a=="boolean"||a===""?o?t.setProperty(n,""):n==="float"?t.cssFloat="":t[n]="":o?t.setProperty(n,a):typeof a!="number"||a===0||cn.has(n)?n==="float"?t.cssFloat=a:t[n]=(""+a).trim():t[n]=a+"px"}function Ji(t,n,a){if(n!=null&&typeof n!="object")throw Error(r(62));if(t=t.style,a!=null){for(var o in a)!a.hasOwnProperty(o)||n!=null&&n.hasOwnProperty(o)||(o.indexOf("--")===0?t.setProperty(o,""):o==="float"?t.cssFloat="":t[o]="");for(var u in n)o=n[u],n.hasOwnProperty(u)&&a[u]!==o&&Ti(t,u,o)}else for(var h in n)n.hasOwnProperty(h)&&Ti(t,h,n[h])}function Ks(t){if(t.indexOf("-")===-1)return!1;switch(t){case"annotation-xml":case"color-profile":case"font-face":case"font-face-src":case"font-face-uri":case"font-face-format":case"font-face-name":case"missing-glyph":return!1;default:return!0}}var Fx=new Map([["acceptCharset","accept-charset"],["htmlFor","for"],["httpEquiv","http-equiv"],["crossOrigin","crossorigin"],["accentHeight","accent-height"],["alignmentBaseline","alignment-baseline"],["arabicForm","arabic-form"],["baselineShift","baseline-shift"],["capHeight","cap-height"],["clipPath","clip-path"],["clipRule","clip-rule"],["colorInterpolation","color-interpolation"],["colorInterpolationFilters","color-interpolation-filters"],["colorProfile","color-profile"],["colorRendering","color-rendering"],["dominantBaseline","dominant-baseline"],["enableBackground","enable-background"],["fillOpacity","fill-opacity"],["fillRule","fill-rule"],["floodColor","flood-color"],["floodOpacity","flood-opacity"],["fontFamily","font-family"],["fontSize","font-size"],["fontSizeAdjust","font-size-adjust"],["fontStretch","font-stretch"],["fontStyle","font-style"],["fontVariant","font-variant"],["fontWeight","font-weight"],["glyphName","glyph-name"],["glyphOrientationHorizontal","glyph-orientation-horizontal"],["glyphOrientationVertical","glyph-orientation-vertical"],["horizAdvX","horiz-adv-x"],["horizOriginX","horiz-origin-x"],["imageRendering","image-rendering"],["letterSpacing","letter-spacing"],["lightingColor","lighting-color"],["markerEnd","marker-end"],["markerMid","marker-mid"],["markerStart","marker-start"],["overlinePosition","overline-position"],["overlineThickness","overline-thickness"],["paintOrder","paint-order"],["panose-1","panose-1"],["pointerEvents","pointer-events"],["renderingIntent","rendering-intent"],["shapeRendering","shape-rendering"],["stopColor","stop-color"],["stopOpacity","stop-opacity"],["strikethroughPosition","strikethrough-position"],["strikethroughThickness","strikethrough-thickness"],["strokeDasharray","stroke-dasharray"],["strokeDashoffset","stroke-dashoffset"],["strokeLinecap","stroke-linecap"],["strokeLinejoin","stroke-linejoin"],["strokeMiterlimit","stroke-miterlimit"],["strokeOpacity","stroke-opacity"],["strokeWidth","stroke-width"],["textAnchor","text-anchor"],["textDecoration","text-decoration"],["textRendering","text-rendering"],["transformOrigin","transform-origin"],["underlinePosition","underline-position"],["underlineThickness","underline-thickness"],["unicodeBidi","unicode-bidi"],["unicodeRange","unicode-range"],["unitsPerEm","units-per-em"],["vAlphabetic","v-alphabetic"],["vHanging","v-hanging"],["vIdeographic","v-ideographic"],["vMathematical","v-mathematical"],["vectorEffect","vector-effect"],["vertAdvY","vert-adv-y"],["vertOriginX","vert-origin-x"],["vertOriginY","vert-origin-y"],["wordSpacing","word-spacing"],["writingMode","writing-mode"],["xmlnsXlink","xmlns:xlink"],["xHeight","x-height"]]),Ix=/^[\u0000-\u001F ]*j[\r\n\t]*a[\r\n\t]*v[\r\n\t]*a[\r\n\t]*s[\r\n\t]*c[\r\n\t]*r[\r\n\t]*i[\r\n\t]*p[\r\n\t]*t[\r\n\t]*:/i;function yl(t){return Ix.test(""+t)?"javascript:throw new Error('React has blocked a javascript: URL as a security precaution.')":t}function $i(){}var bu=null;function Tu(t){return t=t.target||t.srcElement||window,t.correspondingUseElement&&(t=t.correspondingUseElement),t.nodeType===3?t.parentNode:t}var Qs=null,Js=null;function Op(t){var n=Oa(t);if(n&&(t=n.stateNode)){var a=t[mn]||null;e:switch(t=n.stateNode,n.type){case"input":if(Pn(t,a.value,a.defaultValue,a.defaultValue,a.checked,a.defaultChecked,a.type,a.name),n=a.name,a.type==="radio"&&n!=null){for(a=t;a.parentNode;)a=a.parentNode;for(a=a.querySelectorAll('input[name="'+at(""+n)+'"][type="radio"]'),n=0;n<a.length;n++){var o=a[n];if(o!==t&&o.form===t.form){var u=o[mn]||null;if(!u)throw Error(r(90));Pn(o,u.value,u.defaultValue,u.defaultValue,u.checked,u.defaultChecked,u.type,u.name)}}for(n=0;n<a.length;n++)o=a[n],o.form===t.form&&gn(o)}break e;case"textarea":Pt(t,a.value,a.defaultValue);break e;case"select":n=a.value,n!=null&&Jn(t,!!a.multiple,n,!1)}}}var Au=!1;function Pp(t,n,a){if(Au)return t(n,a);Au=!0;try{var o=t(n);return o}finally{if(Au=!1,(Qs!==null||Js!==null)&&(oc(),Qs&&(n=Qs,t=Js,Js=Qs=null,Op(n),t)))for(n=0;n<t.length;n++)Op(t[n])}}function io(t,n){var a=t.stateNode;if(a===null)return null;var o=a[mn]||null;if(o===null)return null;a=o[n];e:switch(n){case"onClick":case"onClickCapture":case"onDoubleClick":case"onDoubleClickCapture":case"onMouseDown":case"onMouseDownCapture":case"onMouseMove":case"onMouseMoveCapture":case"onMouseUp":case"onMouseUpCapture":case"onMouseEnter":(o=!o.disabled)||(t=t.type,o=!(t==="button"||t==="input"||t==="select"||t==="textarea")),t=!o;break e;default:t=!1}if(t)return null;if(a&&typeof a!="function")throw Error(r(231,n,typeof a));return a}var ea=!(typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"),Ru=!1;if(ea)try{var ao={};Object.defineProperty(ao,"passive",{get:function(){Ru=!0}}),window.addEventListener("test",ao,ao),window.removeEventListener("test",ao,ao)}catch{Ru=!1}var Pa=null,Cu=null,Sl=null;function Fp(){if(Sl)return Sl;var t,n=Cu,a=n.length,o,u="value"in Pa?Pa.value:Pa.textContent,h=u.length;for(t=0;t<a&&n[t]===u[t];t++);var S=a-t;for(o=1;o<=S&&n[a-o]===u[h-o];o++);return Sl=u.slice(t,1<o?1-o:void 0)}function Ml(t){var n=t.keyCode;return"charCode"in t?(t=t.charCode,t===0&&n===13&&(t=13)):t=n,t===10&&(t=13),32<=t||t===13?t:0}function El(){return!0}function Ip(){return!1}function Hn(t){function n(a,o,u,h,S){this._reactName=a,this._targetInst=u,this.type=o,this.nativeEvent=h,this.target=S,this.currentTarget=null;for(var D in t)t.hasOwnProperty(D)&&(a=t[D],this[D]=a?a(h):h[D]);return this.isDefaultPrevented=(h.defaultPrevented!=null?h.defaultPrevented:h.returnValue===!1)?El:Ip,this.isPropagationStopped=Ip,this}return v(n.prototype,{preventDefault:function(){this.defaultPrevented=!0;var a=this.nativeEvent;a&&(a.preventDefault?a.preventDefault():typeof a.returnValue!="unknown"&&(a.returnValue=!1),this.isDefaultPrevented=El)},stopPropagation:function(){var a=this.nativeEvent;a&&(a.stopPropagation?a.stopPropagation():typeof a.cancelBubble!="unknown"&&(a.cancelBubble=!0),this.isPropagationStopped=El)},persist:function(){},isPersistent:El}),n}var vs={eventPhase:0,bubbles:0,cancelable:0,timeStamp:function(t){return t.timeStamp||Date.now()},defaultPrevented:0,isTrusted:0},bl=Hn(vs),so=v({},vs,{view:0,detail:0}),zx=Hn(so),wu,Du,ro,Tl=v({},so,{screenX:0,screenY:0,clientX:0,clientY:0,pageX:0,pageY:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,getModifierState:Uu,button:0,buttons:0,relatedTarget:function(t){return t.relatedTarget===void 0?t.fromElement===t.srcElement?t.toElement:t.fromElement:t.relatedTarget},movementX:function(t){return"movementX"in t?t.movementX:(t!==ro&&(ro&&t.type==="mousemove"?(wu=t.screenX-ro.screenX,Du=t.screenY-ro.screenY):Du=wu=0,ro=t),wu)},movementY:function(t){return"movementY"in t?t.movementY:Du}}),zp=Hn(Tl),Bx=v({},Tl,{dataTransfer:0}),Hx=Hn(Bx),Gx=v({},so,{relatedTarget:0}),Nu=Hn(Gx),Vx=v({},vs,{animationName:0,elapsedTime:0,pseudoElement:0}),kx=Hn(Vx),jx=v({},vs,{clipboardData:function(t){return"clipboardData"in t?t.clipboardData:window.clipboardData}}),Xx=Hn(jx),Wx=v({},vs,{data:0}),Bp=Hn(Wx),qx={Esc:"Escape",Spacebar:" ",Left:"ArrowLeft",Up:"ArrowUp",Right:"ArrowRight",Down:"ArrowDown",Del:"Delete",Win:"OS",Menu:"ContextMenu",Apps:"ContextMenu",Scroll:"ScrollLock",MozPrintableKey:"Unidentified"},Yx={8:"Backspace",9:"Tab",12:"Clear",13:"Enter",16:"Shift",17:"Control",18:"Alt",19:"Pause",20:"CapsLock",27:"Escape",32:" ",33:"PageUp",34:"PageDown",35:"End",36:"Home",37:"ArrowLeft",38:"ArrowUp",39:"ArrowRight",40:"ArrowDown",45:"Insert",46:"Delete",112:"F1",113:"F2",114:"F3",115:"F4",116:"F5",117:"F6",118:"F7",119:"F8",120:"F9",121:"F10",122:"F11",123:"F12",144:"NumLock",145:"ScrollLock",224:"Meta"},Zx={Alt:"altKey",Control:"ctrlKey",Meta:"metaKey",Shift:"shiftKey"};function Kx(t){var n=this.nativeEvent;return n.getModifierState?n.getModifierState(t):(t=Zx[t])?!!n[t]:!1}function Uu(){return Kx}var Qx=v({},so,{key:function(t){if(t.key){var n=qx[t.key]||t.key;if(n!=="Unidentified")return n}return t.type==="keypress"?(t=Ml(t),t===13?"Enter":String.fromCharCode(t)):t.type==="keydown"||t.type==="keyup"?Yx[t.keyCode]||"Unidentified":""},code:0,location:0,ctrlKey:0,shiftKey:0,altKey:0,metaKey:0,repeat:0,locale:0,getModifierState:Uu,charCode:function(t){return t.type==="keypress"?Ml(t):0},keyCode:function(t){return t.type==="keydown"||t.type==="keyup"?t.keyCode:0},which:function(t){return t.type==="keypress"?Ml(t):t.type==="keydown"||t.type==="keyup"?t.keyCode:0}}),Jx=Hn(Qx),$x=v({},Tl,{pointerId:0,width:0,height:0,pressure:0,tangentialPressure:0,tiltX:0,tiltY:0,twist:0,pointerType:0,isPrimary:0}),Hp=Hn($x),ey=v({},so,{touches:0,targetTouches:0,changedTouches:0,altKey:0,metaKey:0,ctrlKey:0,shiftKey:0,getModifierState:Uu}),ty=Hn(ey),ny=v({},vs,{propertyName:0,elapsedTime:0,pseudoElement:0}),iy=Hn(ny),ay=v({},Tl,{deltaX:function(t){return"deltaX"in t?t.deltaX:"wheelDeltaX"in t?-t.wheelDeltaX:0},deltaY:function(t){return"deltaY"in t?t.deltaY:"wheelDeltaY"in t?-t.wheelDeltaY:"wheelDelta"in t?-t.wheelDelta:0},deltaZ:0,deltaMode:0}),sy=Hn(ay),ry=v({},vs,{newState:0,oldState:0}),oy=Hn(ry),ly=[9,13,27,32],Lu=ea&&"CompositionEvent"in window,oo=null;ea&&"documentMode"in document&&(oo=document.documentMode);var cy=ea&&"TextEvent"in window&&!oo,Gp=ea&&(!Lu||oo&&8<oo&&11>=oo),Vp=" ",kp=!1;function jp(t,n){switch(t){case"keyup":return ly.indexOf(n.keyCode)!==-1;case"keydown":return n.keyCode!==229;case"keypress":case"mousedown":case"focusout":return!0;default:return!1}}function Xp(t){return t=t.detail,typeof t=="object"&&"data"in t?t.data:null}var $s=!1;function uy(t,n){switch(t){case"compositionend":return Xp(n);case"keypress":return n.which!==32?null:(kp=!0,Vp);case"textInput":return t=n.data,t===Vp&&kp?null:t;default:return null}}function fy(t,n){if($s)return t==="compositionend"||!Lu&&jp(t,n)?(t=Fp(),Sl=Cu=Pa=null,$s=!1,t):null;switch(t){case"paste":return null;case"keypress":if(!(n.ctrlKey||n.altKey||n.metaKey)||n.ctrlKey&&n.altKey){if(n.char&&1<n.char.length)return n.char;if(n.which)return String.fromCharCode(n.which)}return null;case"compositionend":return Gp&&n.locale!=="ko"?null:n.data;default:return null}}var hy={color:!0,date:!0,datetime:!0,"datetime-local":!0,email:!0,month:!0,number:!0,password:!0,range:!0,search:!0,tel:!0,text:!0,time:!0,url:!0,week:!0};function Wp(t){var n=t&&t.nodeName&&t.nodeName.toLowerCase();return n==="input"?!!hy[t.type]:n==="textarea"}function qp(t,n,a,o){Qs?Js?Js.push(o):Js=[o]:Qs=o,n=pc(n,"onChange"),0<n.length&&(a=new bl("onChange","change",null,a,o),t.push({event:a,listeners:n}))}var lo=null,co=null;function dy(t){w_(t,0)}function Al(t){var n=_s(t);if(gn(n))return t}function Yp(t,n){if(t==="change")return n}var Zp=!1;if(ea){var Ou;if(ea){var Pu="oninput"in document;if(!Pu){var Kp=document.createElement("div");Kp.setAttribute("oninput","return;"),Pu=typeof Kp.oninput=="function"}Ou=Pu}else Ou=!1;Zp=Ou&&(!document.documentMode||9<document.documentMode)}function Qp(){lo&&(lo.detachEvent("onpropertychange",Jp),co=lo=null)}function Jp(t){if(t.propertyName==="value"&&Al(co)){var n=[];qp(n,co,t,Tu(t)),Pp(dy,n)}}function py(t,n,a){t==="focusin"?(Qp(),lo=n,co=a,lo.attachEvent("onpropertychange",Jp)):t==="focusout"&&Qp()}function my(t){if(t==="selectionchange"||t==="keyup"||t==="keydown")return Al(co)}function gy(t,n){if(t==="click")return Al(n)}function _y(t,n){if(t==="input"||t==="change")return Al(n)}function vy(t,n){return t===n&&(t!==0||1/t===1/n)||t!==t&&n!==n}var $n=typeof Object.is=="function"?Object.is:vy;function uo(t,n){if($n(t,n))return!0;if(typeof t!="object"||t===null||typeof n!="object"||n===null)return!1;var a=Object.keys(t),o=Object.keys(n);if(a.length!==o.length)return!1;for(o=0;o<a.length;o++){var u=a[o];if(!qt.call(n,u)||!$n(t[u],n[u]))return!1}return!0}function $p(t){for(;t&&t.firstChild;)t=t.firstChild;return t}function em(t,n){var a=$p(t);t=0;for(var o;a;){if(a.nodeType===3){if(o=t+a.textContent.length,t<=n&&o>=n)return{node:a,offset:n-t};t=o}e:{for(;a;){if(a.nextSibling){a=a.nextSibling;break e}a=a.parentNode}a=void 0}a=$p(a)}}function tm(t,n){return t&&n?t===n?!0:t&&t.nodeType===3?!1:n&&n.nodeType===3?tm(t,n.parentNode):"contains"in t?t.contains(n):t.compareDocumentPosition?!!(t.compareDocumentPosition(n)&16):!1:!1}function nm(t){t=t!=null&&t.ownerDocument!=null&&t.ownerDocument.defaultView!=null?t.ownerDocument.defaultView:window;for(var n=je(t.document);n instanceof t.HTMLIFrameElement;){try{var a=typeof n.contentWindow.location.href=="string"}catch{a=!1}if(a)t=n.contentWindow;else break;n=je(t.document)}return n}function Fu(t){var n=t&&t.nodeName&&t.nodeName.toLowerCase();return n&&(n==="input"&&(t.type==="text"||t.type==="search"||t.type==="tel"||t.type==="url"||t.type==="password")||n==="textarea"||t.contentEditable==="true")}var xy=ea&&"documentMode"in document&&11>=document.documentMode,er=null,Iu=null,fo=null,zu=!1;function im(t,n,a){var o=a.window===a?a.document:a.nodeType===9?a:a.ownerDocument;zu||er==null||er!==je(o)||(o=er,"selectionStart"in o&&Fu(o)?o={start:o.selectionStart,end:o.selectionEnd}:(o=(o.ownerDocument&&o.ownerDocument.defaultView||window).getSelection(),o={anchorNode:o.anchorNode,anchorOffset:o.anchorOffset,focusNode:o.focusNode,focusOffset:o.focusOffset}),fo&&uo(fo,o)||(fo=o,o=pc(Iu,"onSelect"),0<o.length&&(n=new bl("onSelect","select",null,n,a),t.push({event:n,listeners:o}),n.target=er)))}function xs(t,n){var a={};return a[t.toLowerCase()]=n.toLowerCase(),a["Webkit"+t]="webkit"+n,a["Moz"+t]="moz"+n,a}var tr={animationend:xs("Animation","AnimationEnd"),animationiteration:xs("Animation","AnimationIteration"),animationstart:xs("Animation","AnimationStart"),transitionrun:xs("Transition","TransitionRun"),transitionstart:xs("Transition","TransitionStart"),transitioncancel:xs("Transition","TransitionCancel"),transitionend:xs("Transition","TransitionEnd")},Bu={},am={};ea&&(am=document.createElement("div").style,"AnimationEvent"in window||(delete tr.animationend.animation,delete tr.animationiteration.animation,delete tr.animationstart.animation),"TransitionEvent"in window||delete tr.transitionend.transition);function ys(t){if(Bu[t])return Bu[t];if(!tr[t])return t;var n=tr[t],a;for(a in n)if(n.hasOwnProperty(a)&&a in am)return Bu[t]=n[a];return t}var sm=ys("animationend"),rm=ys("animationiteration"),om=ys("animationstart"),yy=ys("transitionrun"),Sy=ys("transitionstart"),My=ys("transitioncancel"),lm=ys("transitionend"),cm=new Map,Hu="abort auxClick beforeToggle cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");Hu.push("scrollEnd");function Ai(t,n){cm.set(t,n),te(n,[t])}var Rl=typeof reportError=="function"?reportError:function(t){if(typeof window=="object"&&typeof window.ErrorEvent=="function"){var n=new window.ErrorEvent("error",{bubbles:!0,cancelable:!0,message:typeof t=="object"&&t!==null&&typeof t.message=="string"?String(t.message):String(t),error:t});if(!window.dispatchEvent(n))return}else if(typeof process=="object"&&typeof process.emit=="function"){process.emit("uncaughtException",t);return}console.error(t)},ci=[],nr=0,Gu=0;function Cl(){for(var t=nr,n=Gu=nr=0;n<t;){var a=ci[n];ci[n++]=null;var o=ci[n];ci[n++]=null;var u=ci[n];ci[n++]=null;var h=ci[n];if(ci[n++]=null,o!==null&&u!==null){var S=o.pending;S===null?u.next=u:(u.next=S.next,S.next=u),o.pending=u}h!==0&&um(a,u,h)}}function wl(t,n,a,o){ci[nr++]=t,ci[nr++]=n,ci[nr++]=a,ci[nr++]=o,Gu|=o,t.lanes|=o,t=t.alternate,t!==null&&(t.lanes|=o)}function Vu(t,n,a,o){return wl(t,n,a,o),Dl(t)}function Ss(t,n){return wl(t,null,null,n),Dl(t)}function um(t,n,a){t.lanes|=a;var o=t.alternate;o!==null&&(o.lanes|=a);for(var u=!1,h=t.return;h!==null;)h.childLanes|=a,o=h.alternate,o!==null&&(o.childLanes|=a),h.tag===22&&(t=h.stateNode,t===null||t._visibility&1||(u=!0)),t=h,h=h.return;return t.tag===3?(h=t.stateNode,u&&n!==null&&(u=31-Pe(a),t=h.hiddenUpdates,o=t[u],o===null?t[u]=[n]:o.push(n),n.lane=a|536870912),h):null}function Dl(t){if(50<Oo)throw Oo=0,Jf=null,Error(r(185));for(var n=t.return;n!==null;)t=n,n=t.return;return t.tag===3?t.stateNode:null}var ir={};function Ey(t,n,a,o){this.tag=t,this.key=a,this.sibling=this.child=this.return=this.stateNode=this.type=this.elementType=null,this.index=0,this.refCleanup=this.ref=null,this.pendingProps=n,this.dependencies=this.memoizedState=this.updateQueue=this.memoizedProps=null,this.mode=o,this.subtreeFlags=this.flags=0,this.deletions=null,this.childLanes=this.lanes=0,this.alternate=null}function ei(t,n,a,o){return new Ey(t,n,a,o)}function ku(t){return t=t.prototype,!(!t||!t.isReactComponent)}function ta(t,n){var a=t.alternate;return a===null?(a=ei(t.tag,n,t.key,t.mode),a.elementType=t.elementType,a.type=t.type,a.stateNode=t.stateNode,a.alternate=t,t.alternate=a):(a.pendingProps=n,a.type=t.type,a.flags=0,a.subtreeFlags=0,a.deletions=null),a.flags=t.flags&65011712,a.childLanes=t.childLanes,a.lanes=t.lanes,a.child=t.child,a.memoizedProps=t.memoizedProps,a.memoizedState=t.memoizedState,a.updateQueue=t.updateQueue,n=t.dependencies,a.dependencies=n===null?null:{lanes:n.lanes,firstContext:n.firstContext},a.sibling=t.sibling,a.index=t.index,a.ref=t.ref,a.refCleanup=t.refCleanup,a}function fm(t,n){t.flags&=65011714;var a=t.alternate;return a===null?(t.childLanes=0,t.lanes=n,t.child=null,t.subtreeFlags=0,t.memoizedProps=null,t.memoizedState=null,t.updateQueue=null,t.dependencies=null,t.stateNode=null):(t.childLanes=a.childLanes,t.lanes=a.lanes,t.child=a.child,t.subtreeFlags=0,t.deletions=null,t.memoizedProps=a.memoizedProps,t.memoizedState=a.memoizedState,t.updateQueue=a.updateQueue,t.type=a.type,n=a.dependencies,t.dependencies=n===null?null:{lanes:n.lanes,firstContext:n.firstContext}),t}function Nl(t,n,a,o,u,h){var S=0;if(o=t,typeof t=="function")ku(t)&&(S=1);else if(typeof t=="string")S=CS(t,a,he.current)?26:t==="html"||t==="head"||t==="body"?27:5;else e:switch(t){case L:return t=ei(31,a,n,u),t.elementType=L,t.lanes=h,t;case R:return Ms(a.children,u,h,n);case x:S=8,u|=24;break;case y:return t=ei(12,a,n,u|2),t.elementType=y,t.lanes=h,t;case V:return t=ei(13,a,n,u),t.elementType=V,t.lanes=h,t;case H:return t=ei(19,a,n,u),t.elementType=H,t.lanes=h,t;default:if(typeof t=="object"&&t!==null)switch(t.$$typeof){case U:S=10;break e;case T:S=9;break e;case P:S=11;break e;case z:S=14;break e;case A:S=16,o=null;break e}S=29,a=Error(r(130,t===null?"null":typeof t,"")),o=null}return n=ei(S,a,n,u),n.elementType=t,n.type=o,n.lanes=h,n}function Ms(t,n,a,o){return t=ei(7,t,o,n),t.lanes=a,t}function ju(t,n,a){return t=ei(6,t,null,n),t.lanes=a,t}function hm(t){var n=ei(18,null,null,0);return n.stateNode=t,n}function Xu(t,n,a){return n=ei(4,t.children!==null?t.children:[],t.key,n),n.lanes=a,n.stateNode={containerInfo:t.containerInfo,pendingChildren:null,implementation:t.implementation},n}var dm=new WeakMap;function ui(t,n){if(typeof t=="object"&&t!==null){var a=dm.get(t);return a!==void 0?a:(n={value:t,source:n,stack:k(n)},dm.set(t,n),n)}return{value:t,source:n,stack:k(n)}}var ar=[],sr=0,Ul=null,ho=0,fi=[],hi=0,Fa=null,zi=1,Bi="";function na(t,n){ar[sr++]=ho,ar[sr++]=Ul,Ul=t,ho=n}function pm(t,n,a){fi[hi++]=zi,fi[hi++]=Bi,fi[hi++]=Fa,Fa=t;var o=zi;t=Bi;var u=32-Pe(o)-1;o&=~(1<<u),a+=1;var h=32-Pe(n)+u;if(30<h){var S=u-u%5;h=(o&(1<<S)-1).toString(32),o>>=S,u-=S,zi=1<<32-Pe(n)+u|a<<u|o,Bi=h+t}else zi=1<<h|a<<u|o,Bi=t}function Wu(t){t.return!==null&&(na(t,1),pm(t,1,0))}function qu(t){for(;t===Ul;)Ul=ar[--sr],ar[sr]=null,ho=ar[--sr],ar[sr]=null;for(;t===Fa;)Fa=fi[--hi],fi[hi]=null,Bi=fi[--hi],fi[hi]=null,zi=fi[--hi],fi[hi]=null}function mm(t,n){fi[hi++]=zi,fi[hi++]=Bi,fi[hi++]=Fa,zi=n.id,Bi=n.overflow,Fa=t}var En=null,Xt=null,Et=!1,Ia=null,di=!1,Yu=Error(r(519));function za(t){var n=Error(r(418,1<arguments.length&&arguments[1]!==void 0&&arguments[1]?"text":"HTML",""));throw po(ui(n,t)),Yu}function gm(t){var n=t.stateNode,a=t.type,o=t.memoizedProps;switch(n[on]=t,n[mn]=o,a){case"dialog":vt("cancel",n),vt("close",n);break;case"iframe":case"object":case"embed":vt("load",n);break;case"video":case"audio":for(a=0;a<Fo.length;a++)vt(Fo[a],n);break;case"source":vt("error",n);break;case"img":case"image":case"link":vt("error",n),vt("load",n);break;case"details":vt("toggle",n);break;case"input":vt("invalid",n),Qn(n,o.value,o.defaultValue,o.checked,o.defaultChecked,o.type,o.name,!0);break;case"select":vt("invalid",n);break;case"textarea":vt("invalid",n),ln(n,o.value,o.defaultValue,o.children)}a=o.children,typeof a!="string"&&typeof a!="number"&&typeof a!="bigint"||n.textContent===""+a||o.suppressHydrationWarning===!0||L_(n.textContent,a)?(o.popover!=null&&(vt("beforetoggle",n),vt("toggle",n)),o.onScroll!=null&&vt("scroll",n),o.onScrollEnd!=null&&vt("scrollend",n),o.onClick!=null&&(n.onclick=$i),n=!0):n=!1,n||za(t,!0)}function _m(t){for(En=t.return;En;)switch(En.tag){case 5:case 31:case 13:di=!1;return;case 27:case 3:di=!0;return;default:En=En.return}}function rr(t){if(t!==En)return!1;if(!Et)return _m(t),Et=!0,!1;var n=t.tag,a;if((a=n!==3&&n!==27)&&((a=n===5)&&(a=t.type,a=!(a!=="form"&&a!=="button")||dh(t.type,t.memoizedProps)),a=!a),a&&Xt&&za(t),_m(t),n===13){if(t=t.memoizedState,t=t!==null?t.dehydrated:null,!t)throw Error(r(317));Xt=V_(t)}else if(n===31){if(t=t.memoizedState,t=t!==null?t.dehydrated:null,!t)throw Error(r(317));Xt=V_(t)}else n===27?(n=Xt,Ja(t.type)?(t=vh,vh=null,Xt=t):Xt=n):Xt=En?mi(t.stateNode.nextSibling):null;return!0}function Es(){Xt=En=null,Et=!1}function Zu(){var t=Ia;return t!==null&&(jn===null?jn=t:jn.push.apply(jn,t),Ia=null),t}function po(t){Ia===null?Ia=[t]:Ia.push(t)}var Ku=O(null),bs=null,ia=null;function Ba(t,n,a){ve(Ku,n._currentValue),n._currentValue=a}function aa(t){t._currentValue=Ku.current,j(Ku)}function Qu(t,n,a){for(;t!==null;){var o=t.alternate;if((t.childLanes&n)!==n?(t.childLanes|=n,o!==null&&(o.childLanes|=n)):o!==null&&(o.childLanes&n)!==n&&(o.childLanes|=n),t===a)break;t=t.return}}function Ju(t,n,a,o){var u=t.child;for(u!==null&&(u.return=t);u!==null;){var h=u.dependencies;if(h!==null){var S=u.child;h=h.firstContext;e:for(;h!==null;){var D=h;h=u;for(var G=0;G<n.length;G++)if(D.context===n[G]){h.lanes|=a,D=h.alternate,D!==null&&(D.lanes|=a),Qu(h.return,a,t),o||(S=null);break e}h=D.next}}else if(u.tag===18){if(S=u.return,S===null)throw Error(r(341));S.lanes|=a,h=S.alternate,h!==null&&(h.lanes|=a),Qu(S,a,t),S=null}else S=u.child;if(S!==null)S.return=u;else for(S=u;S!==null;){if(S===t){S=null;break}if(u=S.sibling,u!==null){u.return=S.return,S=u;break}S=S.return}u=S}}function or(t,n,a,o){t=null;for(var u=n,h=!1;u!==null;){if(!h){if((u.flags&524288)!==0)h=!0;else if((u.flags&262144)!==0)break}if(u.tag===10){var S=u.alternate;if(S===null)throw Error(r(387));if(S=S.memoizedProps,S!==null){var D=u.type;$n(u.pendingProps.value,S.value)||(t!==null?t.push(D):t=[D])}}else if(u===Se.current){if(S=u.alternate,S===null)throw Error(r(387));S.memoizedState.memoizedState!==u.memoizedState.memoizedState&&(t!==null?t.push(Go):t=[Go])}u=u.return}t!==null&&Ju(n,t,a,o),n.flags|=262144}function Ll(t){for(t=t.firstContext;t!==null;){if(!$n(t.context._currentValue,t.memoizedValue))return!0;t=t.next}return!1}function Ts(t){bs=t,ia=null,t=t.dependencies,t!==null&&(t.firstContext=null)}function bn(t){return vm(bs,t)}function Ol(t,n){return bs===null&&Ts(t),vm(t,n)}function vm(t,n){var a=n._currentValue;if(n={context:n,memoizedValue:a,next:null},ia===null){if(t===null)throw Error(r(308));ia=n,t.dependencies={lanes:0,firstContext:n},t.flags|=524288}else ia=ia.next=n;return a}var by=typeof AbortController<"u"?AbortController:function(){var t=[],n=this.signal={aborted:!1,addEventListener:function(a,o){t.push(o)}};this.abort=function(){n.aborted=!0,t.forEach(function(a){return a()})}},Ty=s.unstable_scheduleCallback,Ay=s.unstable_NormalPriority,un={$$typeof:U,Consumer:null,Provider:null,_currentValue:null,_currentValue2:null,_threadCount:0};function $u(){return{controller:new by,data:new Map,refCount:0}}function mo(t){t.refCount--,t.refCount===0&&Ty(Ay,function(){t.controller.abort()})}var go=null,ef=0,lr=0,cr=null;function Ry(t,n){if(go===null){var a=go=[];ef=0,lr=ah(),cr={status:"pending",value:void 0,then:function(o){a.push(o)}}}return ef++,n.then(xm,xm),n}function xm(){if(--ef===0&&go!==null){cr!==null&&(cr.status="fulfilled");var t=go;go=null,lr=0,cr=null;for(var n=0;n<t.length;n++)(0,t[n])()}}function Cy(t,n){var a=[],o={status:"pending",value:null,reason:null,then:function(u){a.push(u)}};return t.then(function(){o.status="fulfilled",o.value=n;for(var u=0;u<a.length;u++)(0,a[u])(n)},function(u){for(o.status="rejected",o.reason=u,u=0;u<a.length;u++)(0,a[u])(void 0)}),o}var ym=I.S;I.S=function(t,n){i_=b(),typeof n=="object"&&n!==null&&typeof n.then=="function"&&Ry(t,n),ym!==null&&ym(t,n)};var As=O(null);function tf(){var t=As.current;return t!==null?t:jt.pooledCache}function Pl(t,n){n===null?ve(As,As.current):ve(As,n.pool)}function Sm(){var t=tf();return t===null?null:{parent:un._currentValue,pool:t}}var ur=Error(r(460)),nf=Error(r(474)),Fl=Error(r(542)),Il={then:function(){}};function Mm(t){return t=t.status,t==="fulfilled"||t==="rejected"}function Em(t,n,a){switch(a=t[a],a===void 0?t.push(n):a!==n&&(n.then($i,$i),n=a),n.status){case"fulfilled":return n.value;case"rejected":throw t=n.reason,Tm(t),t;default:if(typeof n.status=="string")n.then($i,$i);else{if(t=jt,t!==null&&100<t.shellSuspendCounter)throw Error(r(482));t=n,t.status="pending",t.then(function(o){if(n.status==="pending"){var u=n;u.status="fulfilled",u.value=o}},function(o){if(n.status==="pending"){var u=n;u.status="rejected",u.reason=o}})}switch(n.status){case"fulfilled":return n.value;case"rejected":throw t=n.reason,Tm(t),t}throw Cs=n,ur}}function Rs(t){try{var n=t._init;return n(t._payload)}catch(a){throw a!==null&&typeof a=="object"&&typeof a.then=="function"?(Cs=a,ur):a}}var Cs=null;function bm(){if(Cs===null)throw Error(r(459));var t=Cs;return Cs=null,t}function Tm(t){if(t===ur||t===Fl)throw Error(r(483))}var fr=null,_o=0;function zl(t){var n=_o;return _o+=1,fr===null&&(fr=[]),Em(fr,t,n)}function vo(t,n){n=n.props.ref,t.ref=n!==void 0?n:null}function Bl(t,n){throw n.$$typeof===g?Error(r(525)):(t=Object.prototype.toString.call(n),Error(r(31,t==="[object Object]"?"object with keys {"+Object.keys(n).join(", ")+"}":t)))}function Am(t){function n(J,X){if(t){var ne=J.deletions;ne===null?(J.deletions=[X],J.flags|=16):ne.push(X)}}function a(J,X){if(!t)return null;for(;X!==null;)n(J,X),X=X.sibling;return null}function o(J){for(var X=new Map;J!==null;)J.key!==null?X.set(J.key,J):X.set(J.index,J),J=J.sibling;return X}function u(J,X){return J=ta(J,X),J.index=0,J.sibling=null,J}function h(J,X,ne){return J.index=ne,t?(ne=J.alternate,ne!==null?(ne=ne.index,ne<X?(J.flags|=67108866,X):ne):(J.flags|=67108866,X)):(J.flags|=1048576,X)}function S(J){return t&&J.alternate===null&&(J.flags|=67108866),J}function D(J,X,ne,ye){return X===null||X.tag!==6?(X=ju(ne,J.mode,ye),X.return=J,X):(X=u(X,ne),X.return=J,X)}function G(J,X,ne,ye){var $e=ne.type;return $e===R?_e(J,X,ne.props.children,ye,ne.key):X!==null&&(X.elementType===$e||typeof $e=="object"&&$e!==null&&$e.$$typeof===A&&Rs($e)===X.type)?(X=u(X,ne.props),vo(X,ne),X.return=J,X):(X=Nl(ne.type,ne.key,ne.props,null,J.mode,ye),vo(X,ne),X.return=J,X)}function ae(J,X,ne,ye){return X===null||X.tag!==4||X.stateNode.containerInfo!==ne.containerInfo||X.stateNode.implementation!==ne.implementation?(X=Xu(ne,J.mode,ye),X.return=J,X):(X=u(X,ne.children||[]),X.return=J,X)}function _e(J,X,ne,ye,$e){return X===null||X.tag!==7?(X=Ms(ne,J.mode,ye,$e),X.return=J,X):(X=u(X,ne),X.return=J,X)}function Me(J,X,ne){if(typeof X=="string"&&X!==""||typeof X=="number"||typeof X=="bigint")return X=ju(""+X,J.mode,ne),X.return=J,X;if(typeof X=="object"&&X!==null){switch(X.$$typeof){case M:return ne=Nl(X.type,X.key,X.props,null,J.mode,ne),vo(ne,X),ne.return=J,ne;case E:return X=Xu(X,J.mode,ne),X.return=J,X;case A:return X=Rs(X),Me(J,X,ne)}if(ee(X)||Y(X))return X=Ms(X,J.mode,ne,null),X.return=J,X;if(typeof X.then=="function")return Me(J,zl(X),ne);if(X.$$typeof===U)return Me(J,Ol(J,X),ne);Bl(J,X)}return null}function le(J,X,ne,ye){var $e=X!==null?X.key:null;if(typeof ne=="string"&&ne!==""||typeof ne=="number"||typeof ne=="bigint")return $e!==null?null:D(J,X,""+ne,ye);if(typeof ne=="object"&&ne!==null){switch(ne.$$typeof){case M:return ne.key===$e?G(J,X,ne,ye):null;case E:return ne.key===$e?ae(J,X,ne,ye):null;case A:return ne=Rs(ne),le(J,X,ne,ye)}if(ee(ne)||Y(ne))return $e!==null?null:_e(J,X,ne,ye,null);if(typeof ne.then=="function")return le(J,X,zl(ne),ye);if(ne.$$typeof===U)return le(J,X,Ol(J,ne),ye);Bl(J,ne)}return null}function ue(J,X,ne,ye,$e){if(typeof ye=="string"&&ye!==""||typeof ye=="number"||typeof ye=="bigint")return J=J.get(ne)||null,D(X,J,""+ye,$e);if(typeof ye=="object"&&ye!==null){switch(ye.$$typeof){case M:return J=J.get(ye.key===null?ne:ye.key)||null,G(X,J,ye,$e);case E:return J=J.get(ye.key===null?ne:ye.key)||null,ae(X,J,ye,$e);case A:return ye=Rs(ye),ue(J,X,ne,ye,$e)}if(ee(ye)||Y(ye))return J=J.get(ne)||null,_e(X,J,ye,$e,null);if(typeof ye.then=="function")return ue(J,X,ne,zl(ye),$e);if(ye.$$typeof===U)return ue(J,X,ne,Ol(X,ye),$e);Bl(X,ye)}return null}function ke(J,X,ne,ye){for(var $e=null,wt=null,Ze=X,ht=X=0,Mt=null;Ze!==null&&ht<ne.length;ht++){Ze.index>ht?(Mt=Ze,Ze=null):Mt=Ze.sibling;var Dt=le(J,Ze,ne[ht],ye);if(Dt===null){Ze===null&&(Ze=Mt);break}t&&Ze&&Dt.alternate===null&&n(J,Ze),X=h(Dt,X,ht),wt===null?$e=Dt:wt.sibling=Dt,wt=Dt,Ze=Mt}if(ht===ne.length)return a(J,Ze),Et&&na(J,ht),$e;if(Ze===null){for(;ht<ne.length;ht++)Ze=Me(J,ne[ht],ye),Ze!==null&&(X=h(Ze,X,ht),wt===null?$e=Ze:wt.sibling=Ze,wt=Ze);return Et&&na(J,ht),$e}for(Ze=o(Ze);ht<ne.length;ht++)Mt=ue(Ze,J,ht,ne[ht],ye),Mt!==null&&(t&&Mt.alternate!==null&&Ze.delete(Mt.key===null?ht:Mt.key),X=h(Mt,X,ht),wt===null?$e=Mt:wt.sibling=Mt,wt=Mt);return t&&Ze.forEach(function(is){return n(J,is)}),Et&&na(J,ht),$e}function et(J,X,ne,ye){if(ne==null)throw Error(r(151));for(var $e=null,wt=null,Ze=X,ht=X=0,Mt=null,Dt=ne.next();Ze!==null&&!Dt.done;ht++,Dt=ne.next()){Ze.index>ht?(Mt=Ze,Ze=null):Mt=Ze.sibling;var is=le(J,Ze,Dt.value,ye);if(is===null){Ze===null&&(Ze=Mt);break}t&&Ze&&is.alternate===null&&n(J,Ze),X=h(is,X,ht),wt===null?$e=is:wt.sibling=is,wt=is,Ze=Mt}if(Dt.done)return a(J,Ze),Et&&na(J,ht),$e;if(Ze===null){for(;!Dt.done;ht++,Dt=ne.next())Dt=Me(J,Dt.value,ye),Dt!==null&&(X=h(Dt,X,ht),wt===null?$e=Dt:wt.sibling=Dt,wt=Dt);return Et&&na(J,ht),$e}for(Ze=o(Ze);!Dt.done;ht++,Dt=ne.next())Dt=ue(Ze,J,ht,Dt.value,ye),Dt!==null&&(t&&Dt.alternate!==null&&Ze.delete(Dt.key===null?ht:Dt.key),X=h(Dt,X,ht),wt===null?$e=Dt:wt.sibling=Dt,wt=Dt);return t&&Ze.forEach(function(BS){return n(J,BS)}),Et&&na(J,ht),$e}function Vt(J,X,ne,ye){if(typeof ne=="object"&&ne!==null&&ne.type===R&&ne.key===null&&(ne=ne.props.children),typeof ne=="object"&&ne!==null){switch(ne.$$typeof){case M:e:{for(var $e=ne.key;X!==null;){if(X.key===$e){if($e=ne.type,$e===R){if(X.tag===7){a(J,X.sibling),ye=u(X,ne.props.children),ye.return=J,J=ye;break e}}else if(X.elementType===$e||typeof $e=="object"&&$e!==null&&$e.$$typeof===A&&Rs($e)===X.type){a(J,X.sibling),ye=u(X,ne.props),vo(ye,ne),ye.return=J,J=ye;break e}a(J,X);break}else n(J,X);X=X.sibling}ne.type===R?(ye=Ms(ne.props.children,J.mode,ye,ne.key),ye.return=J,J=ye):(ye=Nl(ne.type,ne.key,ne.props,null,J.mode,ye),vo(ye,ne),ye.return=J,J=ye)}return S(J);case E:e:{for($e=ne.key;X!==null;){if(X.key===$e)if(X.tag===4&&X.stateNode.containerInfo===ne.containerInfo&&X.stateNode.implementation===ne.implementation){a(J,X.sibling),ye=u(X,ne.children||[]),ye.return=J,J=ye;break e}else{a(J,X);break}else n(J,X);X=X.sibling}ye=Xu(ne,J.mode,ye),ye.return=J,J=ye}return S(J);case A:return ne=Rs(ne),Vt(J,X,ne,ye)}if(ee(ne))return ke(J,X,ne,ye);if(Y(ne)){if($e=Y(ne),typeof $e!="function")throw Error(r(150));return ne=$e.call(ne),et(J,X,ne,ye)}if(typeof ne.then=="function")return Vt(J,X,zl(ne),ye);if(ne.$$typeof===U)return Vt(J,X,Ol(J,ne),ye);Bl(J,ne)}return typeof ne=="string"&&ne!==""||typeof ne=="number"||typeof ne=="bigint"?(ne=""+ne,X!==null&&X.tag===6?(a(J,X.sibling),ye=u(X,ne),ye.return=J,J=ye):(a(J,X),ye=ju(ne,J.mode,ye),ye.return=J,J=ye),S(J)):a(J,X)}return function(J,X,ne,ye){try{_o=0;var $e=Vt(J,X,ne,ye);return fr=null,$e}catch(Ze){if(Ze===ur||Ze===Fl)throw Ze;var wt=ei(29,Ze,null,J.mode);return wt.lanes=ye,wt.return=J,wt}}}var ws=Am(!0),Rm=Am(!1),Ha=!1;function af(t){t.updateQueue={baseState:t.memoizedState,firstBaseUpdate:null,lastBaseUpdate:null,shared:{pending:null,lanes:0,hiddenCallbacks:null},callbacks:null}}function sf(t,n){t=t.updateQueue,n.updateQueue===t&&(n.updateQueue={baseState:t.baseState,firstBaseUpdate:t.firstBaseUpdate,lastBaseUpdate:t.lastBaseUpdate,shared:t.shared,callbacks:null})}function Ga(t){return{lane:t,tag:0,payload:null,callback:null,next:null}}function Va(t,n,a){var o=t.updateQueue;if(o===null)return null;if(o=o.shared,(Ut&2)!==0){var u=o.pending;return u===null?n.next=n:(n.next=u.next,u.next=n),o.pending=n,n=Dl(t),um(t,null,a),n}return wl(t,o,n,a),Dl(t)}function xo(t,n,a){if(n=n.updateQueue,n!==null&&(n=n.shared,(a&4194048)!==0)){var o=n.lanes;o&=t.pendingLanes,a|=o,n.lanes=a,Ws(t,a)}}function rf(t,n){var a=t.updateQueue,o=t.alternate;if(o!==null&&(o=o.updateQueue,a===o)){var u=null,h=null;if(a=a.firstBaseUpdate,a!==null){do{var S={lane:a.lane,tag:a.tag,payload:a.payload,callback:null,next:null};h===null?u=h=S:h=h.next=S,a=a.next}while(a!==null);h===null?u=h=n:h=h.next=n}else u=h=n;a={baseState:o.baseState,firstBaseUpdate:u,lastBaseUpdate:h,shared:o.shared,callbacks:o.callbacks},t.updateQueue=a;return}t=a.lastBaseUpdate,t===null?a.firstBaseUpdate=n:t.next=n,a.lastBaseUpdate=n}var of=!1;function yo(){if(of){var t=cr;if(t!==null)throw t}}function So(t,n,a,o){of=!1;var u=t.updateQueue;Ha=!1;var h=u.firstBaseUpdate,S=u.lastBaseUpdate,D=u.shared.pending;if(D!==null){u.shared.pending=null;var G=D,ae=G.next;G.next=null,S===null?h=ae:S.next=ae,S=G;var _e=t.alternate;_e!==null&&(_e=_e.updateQueue,D=_e.lastBaseUpdate,D!==S&&(D===null?_e.firstBaseUpdate=ae:D.next=ae,_e.lastBaseUpdate=G))}if(h!==null){var Me=u.baseState;S=0,_e=ae=G=null,D=h;do{var le=D.lane&-536870913,ue=le!==D.lane;if(ue?(St&le)===le:(o&le)===le){le!==0&&le===lr&&(of=!0),_e!==null&&(_e=_e.next={lane:0,tag:D.tag,payload:D.payload,callback:null,next:null});e:{var ke=t,et=D;le=n;var Vt=a;switch(et.tag){case 1:if(ke=et.payload,typeof ke=="function"){Me=ke.call(Vt,Me,le);break e}Me=ke;break e;case 3:ke.flags=ke.flags&-65537|128;case 0:if(ke=et.payload,le=typeof ke=="function"?ke.call(Vt,Me,le):ke,le==null)break e;Me=v({},Me,le);break e;case 2:Ha=!0}}le=D.callback,le!==null&&(t.flags|=64,ue&&(t.flags|=8192),ue=u.callbacks,ue===null?u.callbacks=[le]:ue.push(le))}else ue={lane:le,tag:D.tag,payload:D.payload,callback:D.callback,next:null},_e===null?(ae=_e=ue,G=Me):_e=_e.next=ue,S|=le;if(D=D.next,D===null){if(D=u.shared.pending,D===null)break;ue=D,D=ue.next,ue.next=null,u.lastBaseUpdate=ue,u.shared.pending=null}}while(!0);_e===null&&(G=Me),u.baseState=G,u.firstBaseUpdate=ae,u.lastBaseUpdate=_e,h===null&&(u.shared.lanes=0),qa|=S,t.lanes=S,t.memoizedState=Me}}function Cm(t,n){if(typeof t!="function")throw Error(r(191,t));t.call(n)}function wm(t,n){var a=t.callbacks;if(a!==null)for(t.callbacks=null,t=0;t<a.length;t++)Cm(a[t],n)}var hr=O(null),Hl=O(0);function Dm(t,n){t=da,ve(Hl,t),ve(hr,n),da=t|n.baseLanes}function lf(){ve(Hl,da),ve(hr,hr.current)}function cf(){da=Hl.current,j(hr),j(Hl)}var ti=O(null),pi=null;function ka(t){var n=t.alternate;ve(an,an.current&1),ve(ti,t),pi===null&&(n===null||hr.current!==null||n.memoizedState!==null)&&(pi=t)}function uf(t){ve(an,an.current),ve(ti,t),pi===null&&(pi=t)}function Nm(t){t.tag===22?(ve(an,an.current),ve(ti,t),pi===null&&(pi=t)):ja()}function ja(){ve(an,an.current),ve(ti,ti.current)}function ni(t){j(ti),pi===t&&(pi=null),j(an)}var an=O(0);function Gl(t){for(var n=t;n!==null;){if(n.tag===13){var a=n.memoizedState;if(a!==null&&(a=a.dehydrated,a===null||gh(a)||_h(a)))return n}else if(n.tag===19&&(n.memoizedProps.revealOrder==="forwards"||n.memoizedProps.revealOrder==="backwards"||n.memoizedProps.revealOrder==="unstable_legacy-backwards"||n.memoizedProps.revealOrder==="together")){if((n.flags&128)!==0)return n}else if(n.child!==null){n.child.return=n,n=n.child;continue}if(n===t)break;for(;n.sibling===null;){if(n.return===null||n.return===t)return null;n=n.return}n.sibling.return=n.return,n=n.sibling}return null}var sa=0,ct=null,Ht=null,fn=null,Vl=!1,dr=!1,Ds=!1,kl=0,Mo=0,pr=null,wy=0;function en(){throw Error(r(321))}function ff(t,n){if(n===null)return!1;for(var a=0;a<n.length&&a<t.length;a++)if(!$n(t[a],n[a]))return!1;return!0}function hf(t,n,a,o,u,h){return sa=h,ct=n,n.memoizedState=null,n.updateQueue=null,n.lanes=0,I.H=t===null||t.memoizedState===null?pg:Rf,Ds=!1,h=a(o,u),Ds=!1,dr&&(h=Lm(n,a,o,u)),Um(t),h}function Um(t){I.H=To;var n=Ht!==null&&Ht.next!==null;if(sa=0,fn=Ht=ct=null,Vl=!1,Mo=0,pr=null,n)throw Error(r(300));t===null||hn||(t=t.dependencies,t!==null&&Ll(t)&&(hn=!0))}function Lm(t,n,a,o){ct=t;var u=0;do{if(dr&&(pr=null),Mo=0,dr=!1,25<=u)throw Error(r(301));if(u+=1,fn=Ht=null,t.updateQueue!=null){var h=t.updateQueue;h.lastEffect=null,h.events=null,h.stores=null,h.memoCache!=null&&(h.memoCache.index=0)}I.H=mg,h=n(a,o)}while(dr);return h}function Dy(){var t=I.H,n=t.useState()[0];return n=typeof n.then=="function"?Eo(n):n,t=t.useState()[0],(Ht!==null?Ht.memoizedState:null)!==t&&(ct.flags|=1024),n}function df(){var t=kl!==0;return kl=0,t}function pf(t,n,a){n.updateQueue=t.updateQueue,n.flags&=-2053,t.lanes&=~a}function mf(t){if(Vl){for(t=t.memoizedState;t!==null;){var n=t.queue;n!==null&&(n.pending=null),t=t.next}Vl=!1}sa=0,fn=Ht=ct=null,dr=!1,Mo=kl=0,pr=null}function In(){var t={memoizedState:null,baseState:null,baseQueue:null,queue:null,next:null};return fn===null?ct.memoizedState=fn=t:fn=fn.next=t,fn}function sn(){if(Ht===null){var t=ct.alternate;t=t!==null?t.memoizedState:null}else t=Ht.next;var n=fn===null?ct.memoizedState:fn.next;if(n!==null)fn=n,Ht=t;else{if(t===null)throw ct.alternate===null?Error(r(467)):Error(r(310));Ht=t,t={memoizedState:Ht.memoizedState,baseState:Ht.baseState,baseQueue:Ht.baseQueue,queue:Ht.queue,next:null},fn===null?ct.memoizedState=fn=t:fn=fn.next=t}return fn}function jl(){return{lastEffect:null,events:null,stores:null,memoCache:null}}function Eo(t){var n=Mo;return Mo+=1,pr===null&&(pr=[]),t=Em(pr,t,n),n=ct,(fn===null?n.memoizedState:fn.next)===null&&(n=n.alternate,I.H=n===null||n.memoizedState===null?pg:Rf),t}function Xl(t){if(t!==null&&typeof t=="object"){if(typeof t.then=="function")return Eo(t);if(t.$$typeof===U)return bn(t)}throw Error(r(438,String(t)))}function gf(t){var n=null,a=ct.updateQueue;if(a!==null&&(n=a.memoCache),n==null){var o=ct.alternate;o!==null&&(o=o.updateQueue,o!==null&&(o=o.memoCache,o!=null&&(n={data:o.data.map(function(u){return u.slice()}),index:0})))}if(n==null&&(n={data:[],index:0}),a===null&&(a=jl(),ct.updateQueue=a),a.memoCache=n,a=n.data[n.index],a===void 0)for(a=n.data[n.index]=Array(t),o=0;o<t;o++)a[o]=pe;return n.index++,a}function ra(t,n){return typeof n=="function"?n(t):n}function Wl(t){var n=sn();return _f(n,Ht,t)}function _f(t,n,a){var o=t.queue;if(o===null)throw Error(r(311));o.lastRenderedReducer=a;var u=t.baseQueue,h=o.pending;if(h!==null){if(u!==null){var S=u.next;u.next=h.next,h.next=S}n.baseQueue=u=h,o.pending=null}if(h=t.baseState,u===null)t.memoizedState=h;else{n=u.next;var D=S=null,G=null,ae=n,_e=!1;do{var Me=ae.lane&-536870913;if(Me!==ae.lane?(St&Me)===Me:(sa&Me)===Me){var le=ae.revertLane;if(le===0)G!==null&&(G=G.next={lane:0,revertLane:0,gesture:null,action:ae.action,hasEagerState:ae.hasEagerState,eagerState:ae.eagerState,next:null}),Me===lr&&(_e=!0);else if((sa&le)===le){ae=ae.next,le===lr&&(_e=!0);continue}else Me={lane:0,revertLane:ae.revertLane,gesture:null,action:ae.action,hasEagerState:ae.hasEagerState,eagerState:ae.eagerState,next:null},G===null?(D=G=Me,S=h):G=G.next=Me,ct.lanes|=le,qa|=le;Me=ae.action,Ds&&a(h,Me),h=ae.hasEagerState?ae.eagerState:a(h,Me)}else le={lane:Me,revertLane:ae.revertLane,gesture:ae.gesture,action:ae.action,hasEagerState:ae.hasEagerState,eagerState:ae.eagerState,next:null},G===null?(D=G=le,S=h):G=G.next=le,ct.lanes|=Me,qa|=Me;ae=ae.next}while(ae!==null&&ae!==n);if(G===null?S=h:G.next=D,!$n(h,t.memoizedState)&&(hn=!0,_e&&(a=cr,a!==null)))throw a;t.memoizedState=h,t.baseState=S,t.baseQueue=G,o.lastRenderedState=h}return u===null&&(o.lanes=0),[t.memoizedState,o.dispatch]}function vf(t){var n=sn(),a=n.queue;if(a===null)throw Error(r(311));a.lastRenderedReducer=t;var o=a.dispatch,u=a.pending,h=n.memoizedState;if(u!==null){a.pending=null;var S=u=u.next;do h=t(h,S.action),S=S.next;while(S!==u);$n(h,n.memoizedState)||(hn=!0),n.memoizedState=h,n.baseQueue===null&&(n.baseState=h),a.lastRenderedState=h}return[h,o]}function Om(t,n,a){var o=ct,u=sn(),h=Et;if(h){if(a===void 0)throw Error(r(407));a=a()}else a=n();var S=!$n((Ht||u).memoizedState,a);if(S&&(u.memoizedState=a,hn=!0),u=u.queue,Sf(Im.bind(null,o,u,t),[t]),u.getSnapshot!==n||S||fn!==null&&fn.memoizedState.tag&1){if(o.flags|=2048,mr(9,{destroy:void 0},Fm.bind(null,o,u,a,n),null),jt===null)throw Error(r(349));h||(sa&127)!==0||Pm(o,n,a)}return a}function Pm(t,n,a){t.flags|=16384,t={getSnapshot:n,value:a},n=ct.updateQueue,n===null?(n=jl(),ct.updateQueue=n,n.stores=[t]):(a=n.stores,a===null?n.stores=[t]:a.push(t))}function Fm(t,n,a,o){n.value=a,n.getSnapshot=o,zm(n)&&Bm(t)}function Im(t,n,a){return a(function(){zm(n)&&Bm(t)})}function zm(t){var n=t.getSnapshot;t=t.value;try{var a=n();return!$n(t,a)}catch{return!0}}function Bm(t){var n=Ss(t,2);n!==null&&Xn(n,t,2)}function xf(t){var n=In();if(typeof t=="function"){var a=t;if(t=a(),Ds){Fe(!0);try{a()}finally{Fe(!1)}}}return n.memoizedState=n.baseState=t,n.queue={pending:null,lanes:0,dispatch:null,lastRenderedReducer:ra,lastRenderedState:t},n}function Hm(t,n,a,o){return t.baseState=a,_f(t,Ht,typeof o=="function"?o:ra)}function Ny(t,n,a,o,u){if(Zl(t))throw Error(r(485));if(t=n.action,t!==null){var h={payload:u,action:t,next:null,isTransition:!0,status:"pending",value:null,reason:null,listeners:[],then:function(S){h.listeners.push(S)}};I.T!==null?a(!0):h.isTransition=!1,o(h),a=n.pending,a===null?(h.next=n.pending=h,Gm(n,h)):(h.next=a.next,n.pending=a.next=h)}}function Gm(t,n){var a=n.action,o=n.payload,u=t.state;if(n.isTransition){var h=I.T,S={};I.T=S;try{var D=a(u,o),G=I.S;G!==null&&G(S,D),Vm(t,n,D)}catch(ae){yf(t,n,ae)}finally{h!==null&&S.types!==null&&(h.types=S.types),I.T=h}}else try{h=a(u,o),Vm(t,n,h)}catch(ae){yf(t,n,ae)}}function Vm(t,n,a){a!==null&&typeof a=="object"&&typeof a.then=="function"?a.then(function(o){km(t,n,o)},function(o){return yf(t,n,o)}):km(t,n,a)}function km(t,n,a){n.status="fulfilled",n.value=a,jm(n),t.state=a,n=t.pending,n!==null&&(a=n.next,a===n?t.pending=null:(a=a.next,n.next=a,Gm(t,a)))}function yf(t,n,a){var o=t.pending;if(t.pending=null,o!==null){o=o.next;do n.status="rejected",n.reason=a,jm(n),n=n.next;while(n!==o)}t.action=null}function jm(t){t=t.listeners;for(var n=0;n<t.length;n++)(0,t[n])()}function Xm(t,n){return n}function Wm(t,n){if(Et){var a=jt.formState;if(a!==null){e:{var o=ct;if(Et){if(Xt){t:{for(var u=Xt,h=di;u.nodeType!==8;){if(!h){u=null;break t}if(u=mi(u.nextSibling),u===null){u=null;break t}}h=u.data,u=h==="F!"||h==="F"?u:null}if(u){Xt=mi(u.nextSibling),o=u.data==="F!";break e}}za(o)}o=!1}o&&(n=a[0])}}return a=In(),a.memoizedState=a.baseState=n,o={pending:null,lanes:0,dispatch:null,lastRenderedReducer:Xm,lastRenderedState:n},a.queue=o,a=fg.bind(null,ct,o),o.dispatch=a,o=xf(!1),h=Af.bind(null,ct,!1,o.queue),o=In(),u={state:n,dispatch:null,action:t,pending:null},o.queue=u,a=Ny.bind(null,ct,u,h,a),u.dispatch=a,o.memoizedState=t,[n,a,!1]}function qm(t){var n=sn();return Ym(n,Ht,t)}function Ym(t,n,a){if(n=_f(t,n,Xm)[0],t=Wl(ra)[0],typeof n=="object"&&n!==null&&typeof n.then=="function")try{var o=Eo(n)}catch(S){throw S===ur?Fl:S}else o=n;n=sn();var u=n.queue,h=u.dispatch;return a!==n.memoizedState&&(ct.flags|=2048,mr(9,{destroy:void 0},Uy.bind(null,u,a),null)),[o,h,t]}function Uy(t,n){t.action=n}function Zm(t){var n=sn(),a=Ht;if(a!==null)return Ym(n,a,t);sn(),n=n.memoizedState,a=sn();var o=a.queue.dispatch;return a.memoizedState=t,[n,o,!1]}function mr(t,n,a,o){return t={tag:t,create:a,deps:o,inst:n,next:null},n=ct.updateQueue,n===null&&(n=jl(),ct.updateQueue=n),a=n.lastEffect,a===null?n.lastEffect=t.next=t:(o=a.next,a.next=t,t.next=o,n.lastEffect=t),t}function Km(){return sn().memoizedState}function ql(t,n,a,o){var u=In();ct.flags|=t,u.memoizedState=mr(1|n,{destroy:void 0},a,o===void 0?null:o)}function Yl(t,n,a,o){var u=sn();o=o===void 0?null:o;var h=u.memoizedState.inst;Ht!==null&&o!==null&&ff(o,Ht.memoizedState.deps)?u.memoizedState=mr(n,h,a,o):(ct.flags|=t,u.memoizedState=mr(1|n,h,a,o))}function Qm(t,n){ql(8390656,8,t,n)}function Sf(t,n){Yl(2048,8,t,n)}function Ly(t){ct.flags|=4;var n=ct.updateQueue;if(n===null)n=jl(),ct.updateQueue=n,n.events=[t];else{var a=n.events;a===null?n.events=[t]:a.push(t)}}function Jm(t){var n=sn().memoizedState;return Ly({ref:n,nextImpl:t}),function(){if((Ut&2)!==0)throw Error(r(440));return n.impl.apply(void 0,arguments)}}function $m(t,n){return Yl(4,2,t,n)}function eg(t,n){return Yl(4,4,t,n)}function tg(t,n){if(typeof n=="function"){t=t();var a=n(t);return function(){typeof a=="function"?a():n(null)}}if(n!=null)return t=t(),n.current=t,function(){n.current=null}}function ng(t,n,a){a=a!=null?a.concat([t]):null,Yl(4,4,tg.bind(null,n,t),a)}function Mf(){}function ig(t,n){var a=sn();n=n===void 0?null:n;var o=a.memoizedState;return n!==null&&ff(n,o[1])?o[0]:(a.memoizedState=[t,n],t)}function ag(t,n){var a=sn();n=n===void 0?null:n;var o=a.memoizedState;if(n!==null&&ff(n,o[1]))return o[0];if(o=t(),Ds){Fe(!0);try{t()}finally{Fe(!1)}}return a.memoizedState=[o,n],o}function Ef(t,n,a){return a===void 0||(sa&1073741824)!==0&&(St&261930)===0?t.memoizedState=n:(t.memoizedState=a,t=s_(),ct.lanes|=t,qa|=t,a)}function sg(t,n,a,o){return $n(a,n)?a:hr.current!==null?(t=Ef(t,a,o),$n(t,n)||(hn=!0),t):(sa&42)===0||(sa&1073741824)!==0&&(St&261930)===0?(hn=!0,t.memoizedState=a):(t=s_(),ct.lanes|=t,qa|=t,n)}function rg(t,n,a,o,u){var h=B.p;B.p=h!==0&&8>h?h:8;var S=I.T,D={};I.T=D,Af(t,!1,n,a);try{var G=u(),ae=I.S;if(ae!==null&&ae(D,G),G!==null&&typeof G=="object"&&typeof G.then=="function"){var _e=Cy(G,o);bo(t,n,_e,si(t))}else bo(t,n,o,si(t))}catch(Me){bo(t,n,{then:function(){},status:"rejected",reason:Me},si())}finally{B.p=h,S!==null&&D.types!==null&&(S.types=D.types),I.T=S}}function Oy(){}function bf(t,n,a,o){if(t.tag!==5)throw Error(r(476));var u=og(t).queue;rg(t,u,n,$,a===null?Oy:function(){return lg(t),a(o)})}function og(t){var n=t.memoizedState;if(n!==null)return n;n={memoizedState:$,baseState:$,baseQueue:null,queue:{pending:null,lanes:0,dispatch:null,lastRenderedReducer:ra,lastRenderedState:$},next:null};var a={};return n.next={memoizedState:a,baseState:a,baseQueue:null,queue:{pending:null,lanes:0,dispatch:null,lastRenderedReducer:ra,lastRenderedState:a},next:null},t.memoizedState=n,t=t.alternate,t!==null&&(t.memoizedState=n),n}function lg(t){var n=og(t);n.next===null&&(n=t.alternate.memoizedState),bo(t,n.next.queue,{},si())}function Tf(){return bn(Go)}function cg(){return sn().memoizedState}function ug(){return sn().memoizedState}function Py(t){for(var n=t.return;n!==null;){switch(n.tag){case 24:case 3:var a=si();t=Ga(a);var o=Va(n,t,a);o!==null&&(Xn(o,n,a),xo(o,n,a)),n={cache:$u()},t.payload=n;return}n=n.return}}function Fy(t,n,a){var o=si();a={lane:o,revertLane:0,gesture:null,action:a,hasEagerState:!1,eagerState:null,next:null},Zl(t)?hg(n,a):(a=Vu(t,n,a,o),a!==null&&(Xn(a,t,o),dg(a,n,o)))}function fg(t,n,a){var o=si();bo(t,n,a,o)}function bo(t,n,a,o){var u={lane:o,revertLane:0,gesture:null,action:a,hasEagerState:!1,eagerState:null,next:null};if(Zl(t))hg(n,u);else{var h=t.alternate;if(t.lanes===0&&(h===null||h.lanes===0)&&(h=n.lastRenderedReducer,h!==null))try{var S=n.lastRenderedState,D=h(S,a);if(u.hasEagerState=!0,u.eagerState=D,$n(D,S))return wl(t,n,u,0),jt===null&&Cl(),!1}catch{}if(a=Vu(t,n,u,o),a!==null)return Xn(a,t,o),dg(a,n,o),!0}return!1}function Af(t,n,a,o){if(o={lane:2,revertLane:ah(),gesture:null,action:o,hasEagerState:!1,eagerState:null,next:null},Zl(t)){if(n)throw Error(r(479))}else n=Vu(t,a,o,2),n!==null&&Xn(n,t,2)}function Zl(t){var n=t.alternate;return t===ct||n!==null&&n===ct}function hg(t,n){dr=Vl=!0;var a=t.pending;a===null?n.next=n:(n.next=a.next,a.next=n),t.pending=n}function dg(t,n,a){if((a&4194048)!==0){var o=n.lanes;o&=t.pendingLanes,a|=o,n.lanes=a,Ws(t,a)}}var To={readContext:bn,use:Xl,useCallback:en,useContext:en,useEffect:en,useImperativeHandle:en,useLayoutEffect:en,useInsertionEffect:en,useMemo:en,useReducer:en,useRef:en,useState:en,useDebugValue:en,useDeferredValue:en,useTransition:en,useSyncExternalStore:en,useId:en,useHostTransitionStatus:en,useFormState:en,useActionState:en,useOptimistic:en,useMemoCache:en,useCacheRefresh:en};To.useEffectEvent=en;var pg={readContext:bn,use:Xl,useCallback:function(t,n){return In().memoizedState=[t,n===void 0?null:n],t},useContext:bn,useEffect:Qm,useImperativeHandle:function(t,n,a){a=a!=null?a.concat([t]):null,ql(4194308,4,tg.bind(null,n,t),a)},useLayoutEffect:function(t,n){return ql(4194308,4,t,n)},useInsertionEffect:function(t,n){ql(4,2,t,n)},useMemo:function(t,n){var a=In();n=n===void 0?null:n;var o=t();if(Ds){Fe(!0);try{t()}finally{Fe(!1)}}return a.memoizedState=[o,n],o},useReducer:function(t,n,a){var o=In();if(a!==void 0){var u=a(n);if(Ds){Fe(!0);try{a(n)}finally{Fe(!1)}}}else u=n;return o.memoizedState=o.baseState=u,t={pending:null,lanes:0,dispatch:null,lastRenderedReducer:t,lastRenderedState:u},o.queue=t,t=t.dispatch=Fy.bind(null,ct,t),[o.memoizedState,t]},useRef:function(t){var n=In();return t={current:t},n.memoizedState=t},useState:function(t){t=xf(t);var n=t.queue,a=fg.bind(null,ct,n);return n.dispatch=a,[t.memoizedState,a]},useDebugValue:Mf,useDeferredValue:function(t,n){var a=In();return Ef(a,t,n)},useTransition:function(){var t=xf(!1);return t=rg.bind(null,ct,t.queue,!0,!1),In().memoizedState=t,[!1,t]},useSyncExternalStore:function(t,n,a){var o=ct,u=In();if(Et){if(a===void 0)throw Error(r(407));a=a()}else{if(a=n(),jt===null)throw Error(r(349));(St&127)!==0||Pm(o,n,a)}u.memoizedState=a;var h={value:a,getSnapshot:n};return u.queue=h,Qm(Im.bind(null,o,h,t),[t]),o.flags|=2048,mr(9,{destroy:void 0},Fm.bind(null,o,h,a,n),null),a},useId:function(){var t=In(),n=jt.identifierPrefix;if(Et){var a=Bi,o=zi;a=(o&~(1<<32-Pe(o)-1)).toString(32)+a,n="_"+n+"R_"+a,a=kl++,0<a&&(n+="H"+a.toString(32)),n+="_"}else a=wy++,n="_"+n+"r_"+a.toString(32)+"_";return t.memoizedState=n},useHostTransitionStatus:Tf,useFormState:Wm,useActionState:Wm,useOptimistic:function(t){var n=In();n.memoizedState=n.baseState=t;var a={pending:null,lanes:0,dispatch:null,lastRenderedReducer:null,lastRenderedState:null};return n.queue=a,n=Af.bind(null,ct,!0,a),a.dispatch=n,[t,n]},useMemoCache:gf,useCacheRefresh:function(){return In().memoizedState=Py.bind(null,ct)},useEffectEvent:function(t){var n=In(),a={impl:t};return n.memoizedState=a,function(){if((Ut&2)!==0)throw Error(r(440));return a.impl.apply(void 0,arguments)}}},Rf={readContext:bn,use:Xl,useCallback:ig,useContext:bn,useEffect:Sf,useImperativeHandle:ng,useInsertionEffect:$m,useLayoutEffect:eg,useMemo:ag,useReducer:Wl,useRef:Km,useState:function(){return Wl(ra)},useDebugValue:Mf,useDeferredValue:function(t,n){var a=sn();return sg(a,Ht.memoizedState,t,n)},useTransition:function(){var t=Wl(ra)[0],n=sn().memoizedState;return[typeof t=="boolean"?t:Eo(t),n]},useSyncExternalStore:Om,useId:cg,useHostTransitionStatus:Tf,useFormState:qm,useActionState:qm,useOptimistic:function(t,n){var a=sn();return Hm(a,Ht,t,n)},useMemoCache:gf,useCacheRefresh:ug};Rf.useEffectEvent=Jm;var mg={readContext:bn,use:Xl,useCallback:ig,useContext:bn,useEffect:Sf,useImperativeHandle:ng,useInsertionEffect:$m,useLayoutEffect:eg,useMemo:ag,useReducer:vf,useRef:Km,useState:function(){return vf(ra)},useDebugValue:Mf,useDeferredValue:function(t,n){var a=sn();return Ht===null?Ef(a,t,n):sg(a,Ht.memoizedState,t,n)},useTransition:function(){var t=vf(ra)[0],n=sn().memoizedState;return[typeof t=="boolean"?t:Eo(t),n]},useSyncExternalStore:Om,useId:cg,useHostTransitionStatus:Tf,useFormState:Zm,useActionState:Zm,useOptimistic:function(t,n){var a=sn();return Ht!==null?Hm(a,Ht,t,n):(a.baseState=t,[t,a.queue.dispatch])},useMemoCache:gf,useCacheRefresh:ug};mg.useEffectEvent=Jm;function Cf(t,n,a,o){n=t.memoizedState,a=a(o,n),a=a==null?n:v({},n,a),t.memoizedState=a,t.lanes===0&&(t.updateQueue.baseState=a)}var wf={enqueueSetState:function(t,n,a){t=t._reactInternals;var o=si(),u=Ga(o);u.payload=n,a!=null&&(u.callback=a),n=Va(t,u,o),n!==null&&(Xn(n,t,o),xo(n,t,o))},enqueueReplaceState:function(t,n,a){t=t._reactInternals;var o=si(),u=Ga(o);u.tag=1,u.payload=n,a!=null&&(u.callback=a),n=Va(t,u,o),n!==null&&(Xn(n,t,o),xo(n,t,o))},enqueueForceUpdate:function(t,n){t=t._reactInternals;var a=si(),o=Ga(a);o.tag=2,n!=null&&(o.callback=n),n=Va(t,o,a),n!==null&&(Xn(n,t,a),xo(n,t,a))}};function gg(t,n,a,o,u,h,S){return t=t.stateNode,typeof t.shouldComponentUpdate=="function"?t.shouldComponentUpdate(o,h,S):n.prototype&&n.prototype.isPureReactComponent?!uo(a,o)||!uo(u,h):!0}function _g(t,n,a,o){t=n.state,typeof n.componentWillReceiveProps=="function"&&n.componentWillReceiveProps(a,o),typeof n.UNSAFE_componentWillReceiveProps=="function"&&n.UNSAFE_componentWillReceiveProps(a,o),n.state!==t&&wf.enqueueReplaceState(n,n.state,null)}function Ns(t,n){var a=n;if("ref"in n){a={};for(var o in n)o!=="ref"&&(a[o]=n[o])}if(t=t.defaultProps){a===n&&(a=v({},a));for(var u in t)a[u]===void 0&&(a[u]=t[u])}return a}function vg(t){Rl(t)}function xg(t){console.error(t)}function yg(t){Rl(t)}function Kl(t,n){try{var a=t.onUncaughtError;a(n.value,{componentStack:n.stack})}catch(o){setTimeout(function(){throw o})}}function Sg(t,n,a){try{var o=t.onCaughtError;o(a.value,{componentStack:a.stack,errorBoundary:n.tag===1?n.stateNode:null})}catch(u){setTimeout(function(){throw u})}}function Df(t,n,a){return a=Ga(a),a.tag=3,a.payload={element:null},a.callback=function(){Kl(t,n)},a}function Mg(t){return t=Ga(t),t.tag=3,t}function Eg(t,n,a,o){var u=a.type.getDerivedStateFromError;if(typeof u=="function"){var h=o.value;t.payload=function(){return u(h)},t.callback=function(){Sg(n,a,o)}}var S=a.stateNode;S!==null&&typeof S.componentDidCatch=="function"&&(t.callback=function(){Sg(n,a,o),typeof u!="function"&&(Ya===null?Ya=new Set([this]):Ya.add(this));var D=o.stack;this.componentDidCatch(o.value,{componentStack:D!==null?D:""})})}function Iy(t,n,a,o,u){if(a.flags|=32768,o!==null&&typeof o=="object"&&typeof o.then=="function"){if(n=a.alternate,n!==null&&or(n,a,u,!0),a=ti.current,a!==null){switch(a.tag){case 31:case 13:return pi===null?lc():a.alternate===null&&tn===0&&(tn=3),a.flags&=-257,a.flags|=65536,a.lanes=u,o===Il?a.flags|=16384:(n=a.updateQueue,n===null?a.updateQueue=new Set([o]):n.add(o),th(t,o,u)),!1;case 22:return a.flags|=65536,o===Il?a.flags|=16384:(n=a.updateQueue,n===null?(n={transitions:null,markerInstances:null,retryQueue:new Set([o])},a.updateQueue=n):(a=n.retryQueue,a===null?n.retryQueue=new Set([o]):a.add(o)),th(t,o,u)),!1}throw Error(r(435,a.tag))}return th(t,o,u),lc(),!1}if(Et)return n=ti.current,n!==null?((n.flags&65536)===0&&(n.flags|=256),n.flags|=65536,n.lanes=u,o!==Yu&&(t=Error(r(422),{cause:o}),po(ui(t,a)))):(o!==Yu&&(n=Error(r(423),{cause:o}),po(ui(n,a))),t=t.current.alternate,t.flags|=65536,u&=-u,t.lanes|=u,o=ui(o,a),u=Df(t.stateNode,o,u),rf(t,u),tn!==4&&(tn=2)),!1;var h=Error(r(520),{cause:o});if(h=ui(h,a),Lo===null?Lo=[h]:Lo.push(h),tn!==4&&(tn=2),n===null)return!0;o=ui(o,a),a=n;do{switch(a.tag){case 3:return a.flags|=65536,t=u&-u,a.lanes|=t,t=Df(a.stateNode,o,t),rf(a,t),!1;case 1:if(n=a.type,h=a.stateNode,(a.flags&128)===0&&(typeof n.getDerivedStateFromError=="function"||h!==null&&typeof h.componentDidCatch=="function"&&(Ya===null||!Ya.has(h))))return a.flags|=65536,u&=-u,a.lanes|=u,u=Mg(u),Eg(u,t,a,o),rf(a,u),!1}a=a.return}while(a!==null);return!1}var Nf=Error(r(461)),hn=!1;function Tn(t,n,a,o){n.child=t===null?Rm(n,null,a,o):ws(n,t.child,a,o)}function bg(t,n,a,o,u){a=a.render;var h=n.ref;if("ref"in o){var S={};for(var D in o)D!=="ref"&&(S[D]=o[D])}else S=o;return Ts(n),o=hf(t,n,a,S,h,u),D=df(),t!==null&&!hn?(pf(t,n,u),oa(t,n,u)):(Et&&D&&Wu(n),n.flags|=1,Tn(t,n,o,u),n.child)}function Tg(t,n,a,o,u){if(t===null){var h=a.type;return typeof h=="function"&&!ku(h)&&h.defaultProps===void 0&&a.compare===null?(n.tag=15,n.type=h,Ag(t,n,h,o,u)):(t=Nl(a.type,null,o,n,n.mode,u),t.ref=n.ref,t.return=n,n.child=t)}if(h=t.child,!Bf(t,u)){var S=h.memoizedProps;if(a=a.compare,a=a!==null?a:uo,a(S,o)&&t.ref===n.ref)return oa(t,n,u)}return n.flags|=1,t=ta(h,o),t.ref=n.ref,t.return=n,n.child=t}function Ag(t,n,a,o,u){if(t!==null){var h=t.memoizedProps;if(uo(h,o)&&t.ref===n.ref)if(hn=!1,n.pendingProps=o=h,Bf(t,u))(t.flags&131072)!==0&&(hn=!0);else return n.lanes=t.lanes,oa(t,n,u)}return Uf(t,n,a,o,u)}function Rg(t,n,a,o){var u=o.children,h=t!==null?t.memoizedState:null;if(t===null&&n.stateNode===null&&(n.stateNode={_visibility:1,_pendingMarkers:null,_retryCache:null,_transitions:null}),o.mode==="hidden"){if((n.flags&128)!==0){if(h=h!==null?h.baseLanes|a:a,t!==null){for(o=n.child=t.child,u=0;o!==null;)u=u|o.lanes|o.childLanes,o=o.sibling;o=u&~h}else o=0,n.child=null;return Cg(t,n,h,a,o)}if((a&536870912)!==0)n.memoizedState={baseLanes:0,cachePool:null},t!==null&&Pl(n,h!==null?h.cachePool:null),h!==null?Dm(n,h):lf(),Nm(n);else return o=n.lanes=536870912,Cg(t,n,h!==null?h.baseLanes|a:a,a,o)}else h!==null?(Pl(n,h.cachePool),Dm(n,h),ja(),n.memoizedState=null):(t!==null&&Pl(n,null),lf(),ja());return Tn(t,n,u,a),n.child}function Ao(t,n){return t!==null&&t.tag===22||n.stateNode!==null||(n.stateNode={_visibility:1,_pendingMarkers:null,_retryCache:null,_transitions:null}),n.sibling}function Cg(t,n,a,o,u){var h=tf();return h=h===null?null:{parent:un._currentValue,pool:h},n.memoizedState={baseLanes:a,cachePool:h},t!==null&&Pl(n,null),lf(),Nm(n),t!==null&&or(t,n,o,!0),n.childLanes=u,null}function Ql(t,n){return n=$l({mode:n.mode,children:n.children},t.mode),n.ref=t.ref,t.child=n,n.return=t,n}function wg(t,n,a){return ws(n,t.child,null,a),t=Ql(n,n.pendingProps),t.flags|=2,ni(n),n.memoizedState=null,t}function zy(t,n,a){var o=n.pendingProps,u=(n.flags&128)!==0;if(n.flags&=-129,t===null){if(Et){if(o.mode==="hidden")return t=Ql(n,o),n.lanes=536870912,Ao(null,t);if(uf(n),(t=Xt)?(t=G_(t,di),t=t!==null&&t.data==="&"?t:null,t!==null&&(n.memoizedState={dehydrated:t,treeContext:Fa!==null?{id:zi,overflow:Bi}:null,retryLane:536870912,hydrationErrors:null},a=hm(t),a.return=n,n.child=a,En=n,Xt=null)):t=null,t===null)throw za(n);return n.lanes=536870912,null}return Ql(n,o)}var h=t.memoizedState;if(h!==null){var S=h.dehydrated;if(uf(n),u)if(n.flags&256)n.flags&=-257,n=wg(t,n,a);else if(n.memoizedState!==null)n.child=t.child,n.flags|=128,n=null;else throw Error(r(558));else if(hn||or(t,n,a,!1),u=(a&t.childLanes)!==0,hn||u){if(o=jt,o!==null&&(S=gl(o,a),S!==0&&S!==h.retryLane))throw h.retryLane=S,Ss(t,S),Xn(o,t,S),Nf;lc(),n=wg(t,n,a)}else t=h.treeContext,Xt=mi(S.nextSibling),En=n,Et=!0,Ia=null,di=!1,t!==null&&mm(n,t),n=Ql(n,o),n.flags|=4096;return n}return t=ta(t.child,{mode:o.mode,children:o.children}),t.ref=n.ref,n.child=t,t.return=n,t}function Jl(t,n){var a=n.ref;if(a===null)t!==null&&t.ref!==null&&(n.flags|=4194816);else{if(typeof a!="function"&&typeof a!="object")throw Error(r(284));(t===null||t.ref!==a)&&(n.flags|=4194816)}}function Uf(t,n,a,o,u){return Ts(n),a=hf(t,n,a,o,void 0,u),o=df(),t!==null&&!hn?(pf(t,n,u),oa(t,n,u)):(Et&&o&&Wu(n),n.flags|=1,Tn(t,n,a,u),n.child)}function Dg(t,n,a,o,u,h){return Ts(n),n.updateQueue=null,a=Lm(n,o,a,u),Um(t),o=df(),t!==null&&!hn?(pf(t,n,h),oa(t,n,h)):(Et&&o&&Wu(n),n.flags|=1,Tn(t,n,a,h),n.child)}function Ng(t,n,a,o,u){if(Ts(n),n.stateNode===null){var h=ir,S=a.contextType;typeof S=="object"&&S!==null&&(h=bn(S)),h=new a(o,h),n.memoizedState=h.state!==null&&h.state!==void 0?h.state:null,h.updater=wf,n.stateNode=h,h._reactInternals=n,h=n.stateNode,h.props=o,h.state=n.memoizedState,h.refs={},af(n),S=a.contextType,h.context=typeof S=="object"&&S!==null?bn(S):ir,h.state=n.memoizedState,S=a.getDerivedStateFromProps,typeof S=="function"&&(Cf(n,a,S,o),h.state=n.memoizedState),typeof a.getDerivedStateFromProps=="function"||typeof h.getSnapshotBeforeUpdate=="function"||typeof h.UNSAFE_componentWillMount!="function"&&typeof h.componentWillMount!="function"||(S=h.state,typeof h.componentWillMount=="function"&&h.componentWillMount(),typeof h.UNSAFE_componentWillMount=="function"&&h.UNSAFE_componentWillMount(),S!==h.state&&wf.enqueueReplaceState(h,h.state,null),So(n,o,h,u),yo(),h.state=n.memoizedState),typeof h.componentDidMount=="function"&&(n.flags|=4194308),o=!0}else if(t===null){h=n.stateNode;var D=n.memoizedProps,G=Ns(a,D);h.props=G;var ae=h.context,_e=a.contextType;S=ir,typeof _e=="object"&&_e!==null&&(S=bn(_e));var Me=a.getDerivedStateFromProps;_e=typeof Me=="function"||typeof h.getSnapshotBeforeUpdate=="function",D=n.pendingProps!==D,_e||typeof h.UNSAFE_componentWillReceiveProps!="function"&&typeof h.componentWillReceiveProps!="function"||(D||ae!==S)&&_g(n,h,o,S),Ha=!1;var le=n.memoizedState;h.state=le,So(n,o,h,u),yo(),ae=n.memoizedState,D||le!==ae||Ha?(typeof Me=="function"&&(Cf(n,a,Me,o),ae=n.memoizedState),(G=Ha||gg(n,a,G,o,le,ae,S))?(_e||typeof h.UNSAFE_componentWillMount!="function"&&typeof h.componentWillMount!="function"||(typeof h.componentWillMount=="function"&&h.componentWillMount(),typeof h.UNSAFE_componentWillMount=="function"&&h.UNSAFE_componentWillMount()),typeof h.componentDidMount=="function"&&(n.flags|=4194308)):(typeof h.componentDidMount=="function"&&(n.flags|=4194308),n.memoizedProps=o,n.memoizedState=ae),h.props=o,h.state=ae,h.context=S,o=G):(typeof h.componentDidMount=="function"&&(n.flags|=4194308),o=!1)}else{h=n.stateNode,sf(t,n),S=n.memoizedProps,_e=Ns(a,S),h.props=_e,Me=n.pendingProps,le=h.context,ae=a.contextType,G=ir,typeof ae=="object"&&ae!==null&&(G=bn(ae)),D=a.getDerivedStateFromProps,(ae=typeof D=="function"||typeof h.getSnapshotBeforeUpdate=="function")||typeof h.UNSAFE_componentWillReceiveProps!="function"&&typeof h.componentWillReceiveProps!="function"||(S!==Me||le!==G)&&_g(n,h,o,G),Ha=!1,le=n.memoizedState,h.state=le,So(n,o,h,u),yo();var ue=n.memoizedState;S!==Me||le!==ue||Ha||t!==null&&t.dependencies!==null&&Ll(t.dependencies)?(typeof D=="function"&&(Cf(n,a,D,o),ue=n.memoizedState),(_e=Ha||gg(n,a,_e,o,le,ue,G)||t!==null&&t.dependencies!==null&&Ll(t.dependencies))?(ae||typeof h.UNSAFE_componentWillUpdate!="function"&&typeof h.componentWillUpdate!="function"||(typeof h.componentWillUpdate=="function"&&h.componentWillUpdate(o,ue,G),typeof h.UNSAFE_componentWillUpdate=="function"&&h.UNSAFE_componentWillUpdate(o,ue,G)),typeof h.componentDidUpdate=="function"&&(n.flags|=4),typeof h.getSnapshotBeforeUpdate=="function"&&(n.flags|=1024)):(typeof h.componentDidUpdate!="function"||S===t.memoizedProps&&le===t.memoizedState||(n.flags|=4),typeof h.getSnapshotBeforeUpdate!="function"||S===t.memoizedProps&&le===t.memoizedState||(n.flags|=1024),n.memoizedProps=o,n.memoizedState=ue),h.props=o,h.state=ue,h.context=G,o=_e):(typeof h.componentDidUpdate!="function"||S===t.memoizedProps&&le===t.memoizedState||(n.flags|=4),typeof h.getSnapshotBeforeUpdate!="function"||S===t.memoizedProps&&le===t.memoizedState||(n.flags|=1024),o=!1)}return h=o,Jl(t,n),o=(n.flags&128)!==0,h||o?(h=n.stateNode,a=o&&typeof a.getDerivedStateFromError!="function"?null:h.render(),n.flags|=1,t!==null&&o?(n.child=ws(n,t.child,null,u),n.child=ws(n,null,a,u)):Tn(t,n,a,u),n.memoizedState=h.state,t=n.child):t=oa(t,n,u),t}function Ug(t,n,a,o){return Es(),n.flags|=256,Tn(t,n,a,o),n.child}var Lf={dehydrated:null,treeContext:null,retryLane:0,hydrationErrors:null};function Of(t){return{baseLanes:t,cachePool:Sm()}}function Pf(t,n,a){return t=t!==null?t.childLanes&~a:0,n&&(t|=ai),t}function Lg(t,n,a){var o=n.pendingProps,u=!1,h=(n.flags&128)!==0,S;if((S=h)||(S=t!==null&&t.memoizedState===null?!1:(an.current&2)!==0),S&&(u=!0,n.flags&=-129),S=(n.flags&32)!==0,n.flags&=-33,t===null){if(Et){if(u?ka(n):ja(),(t=Xt)?(t=G_(t,di),t=t!==null&&t.data!=="&"?t:null,t!==null&&(n.memoizedState={dehydrated:t,treeContext:Fa!==null?{id:zi,overflow:Bi}:null,retryLane:536870912,hydrationErrors:null},a=hm(t),a.return=n,n.child=a,En=n,Xt=null)):t=null,t===null)throw za(n);return _h(t)?n.lanes=32:n.lanes=536870912,null}var D=o.children;return o=o.fallback,u?(ja(),u=n.mode,D=$l({mode:"hidden",children:D},u),o=Ms(o,u,a,null),D.return=n,o.return=n,D.sibling=o,n.child=D,o=n.child,o.memoizedState=Of(a),o.childLanes=Pf(t,S,a),n.memoizedState=Lf,Ao(null,o)):(ka(n),Ff(n,D))}var G=t.memoizedState;if(G!==null&&(D=G.dehydrated,D!==null)){if(h)n.flags&256?(ka(n),n.flags&=-257,n=If(t,n,a)):n.memoizedState!==null?(ja(),n.child=t.child,n.flags|=128,n=null):(ja(),D=o.fallback,u=n.mode,o=$l({mode:"visible",children:o.children},u),D=Ms(D,u,a,null),D.flags|=2,o.return=n,D.return=n,o.sibling=D,n.child=o,ws(n,t.child,null,a),o=n.child,o.memoizedState=Of(a),o.childLanes=Pf(t,S,a),n.memoizedState=Lf,n=Ao(null,o));else if(ka(n),_h(D)){if(S=D.nextSibling&&D.nextSibling.dataset,S)var ae=S.dgst;S=ae,o=Error(r(419)),o.stack="",o.digest=S,po({value:o,source:null,stack:null}),n=If(t,n,a)}else if(hn||or(t,n,a,!1),S=(a&t.childLanes)!==0,hn||S){if(S=jt,S!==null&&(o=gl(S,a),o!==0&&o!==G.retryLane))throw G.retryLane=o,Ss(t,o),Xn(S,t,o),Nf;gh(D)||lc(),n=If(t,n,a)}else gh(D)?(n.flags|=192,n.child=t.child,n=null):(t=G.treeContext,Xt=mi(D.nextSibling),En=n,Et=!0,Ia=null,di=!1,t!==null&&mm(n,t),n=Ff(n,o.children),n.flags|=4096);return n}return u?(ja(),D=o.fallback,u=n.mode,G=t.child,ae=G.sibling,o=ta(G,{mode:"hidden",children:o.children}),o.subtreeFlags=G.subtreeFlags&65011712,ae!==null?D=ta(ae,D):(D=Ms(D,u,a,null),D.flags|=2),D.return=n,o.return=n,o.sibling=D,n.child=o,Ao(null,o),o=n.child,D=t.child.memoizedState,D===null?D=Of(a):(u=D.cachePool,u!==null?(G=un._currentValue,u=u.parent!==G?{parent:G,pool:G}:u):u=Sm(),D={baseLanes:D.baseLanes|a,cachePool:u}),o.memoizedState=D,o.childLanes=Pf(t,S,a),n.memoizedState=Lf,Ao(t.child,o)):(ka(n),a=t.child,t=a.sibling,a=ta(a,{mode:"visible",children:o.children}),a.return=n,a.sibling=null,t!==null&&(S=n.deletions,S===null?(n.deletions=[t],n.flags|=16):S.push(t)),n.child=a,n.memoizedState=null,a)}function Ff(t,n){return n=$l({mode:"visible",children:n},t.mode),n.return=t,t.child=n}function $l(t,n){return t=ei(22,t,null,n),t.lanes=0,t}function If(t,n,a){return ws(n,t.child,null,a),t=Ff(n,n.pendingProps.children),t.flags|=2,n.memoizedState=null,t}function Og(t,n,a){t.lanes|=n;var o=t.alternate;o!==null&&(o.lanes|=n),Qu(t.return,n,a)}function zf(t,n,a,o,u,h){var S=t.memoizedState;S===null?t.memoizedState={isBackwards:n,rendering:null,renderingStartTime:0,last:o,tail:a,tailMode:u,treeForkCount:h}:(S.isBackwards=n,S.rendering=null,S.renderingStartTime=0,S.last=o,S.tail=a,S.tailMode=u,S.treeForkCount=h)}function Pg(t,n,a){var o=n.pendingProps,u=o.revealOrder,h=o.tail;o=o.children;var S=an.current,D=(S&2)!==0;if(D?(S=S&1|2,n.flags|=128):S&=1,ve(an,S),Tn(t,n,o,a),o=Et?ho:0,!D&&t!==null&&(t.flags&128)!==0)e:for(t=n.child;t!==null;){if(t.tag===13)t.memoizedState!==null&&Og(t,a,n);else if(t.tag===19)Og(t,a,n);else if(t.child!==null){t.child.return=t,t=t.child;continue}if(t===n)break e;for(;t.sibling===null;){if(t.return===null||t.return===n)break e;t=t.return}t.sibling.return=t.return,t=t.sibling}switch(u){case"forwards":for(a=n.child,u=null;a!==null;)t=a.alternate,t!==null&&Gl(t)===null&&(u=a),a=a.sibling;a=u,a===null?(u=n.child,n.child=null):(u=a.sibling,a.sibling=null),zf(n,!1,u,a,h,o);break;case"backwards":case"unstable_legacy-backwards":for(a=null,u=n.child,n.child=null;u!==null;){if(t=u.alternate,t!==null&&Gl(t)===null){n.child=u;break}t=u.sibling,u.sibling=a,a=u,u=t}zf(n,!0,a,null,h,o);break;case"together":zf(n,!1,null,null,void 0,o);break;default:n.memoizedState=null}return n.child}function oa(t,n,a){if(t!==null&&(n.dependencies=t.dependencies),qa|=n.lanes,(a&n.childLanes)===0)if(t!==null){if(or(t,n,a,!1),(a&n.childLanes)===0)return null}else return null;if(t!==null&&n.child!==t.child)throw Error(r(153));if(n.child!==null){for(t=n.child,a=ta(t,t.pendingProps),n.child=a,a.return=n;t.sibling!==null;)t=t.sibling,a=a.sibling=ta(t,t.pendingProps),a.return=n;a.sibling=null}return n.child}function Bf(t,n){return(t.lanes&n)!==0?!0:(t=t.dependencies,!!(t!==null&&Ll(t)))}function By(t,n,a){switch(n.tag){case 3:Ae(n,n.stateNode.containerInfo),Ba(n,un,t.memoizedState.cache),Es();break;case 27:case 5:Qe(n);break;case 4:Ae(n,n.stateNode.containerInfo);break;case 10:Ba(n,n.type,n.memoizedProps.value);break;case 31:if(n.memoizedState!==null)return n.flags|=128,uf(n),null;break;case 13:var o=n.memoizedState;if(o!==null)return o.dehydrated!==null?(ka(n),n.flags|=128,null):(a&n.child.childLanes)!==0?Lg(t,n,a):(ka(n),t=oa(t,n,a),t!==null?t.sibling:null);ka(n);break;case 19:var u=(t.flags&128)!==0;if(o=(a&n.childLanes)!==0,o||(or(t,n,a,!1),o=(a&n.childLanes)!==0),u){if(o)return Pg(t,n,a);n.flags|=128}if(u=n.memoizedState,u!==null&&(u.rendering=null,u.tail=null,u.lastEffect=null),ve(an,an.current),o)break;return null;case 22:return n.lanes=0,Rg(t,n,a,n.pendingProps);case 24:Ba(n,un,t.memoizedState.cache)}return oa(t,n,a)}function Fg(t,n,a){if(t!==null)if(t.memoizedProps!==n.pendingProps)hn=!0;else{if(!Bf(t,a)&&(n.flags&128)===0)return hn=!1,By(t,n,a);hn=(t.flags&131072)!==0}else hn=!1,Et&&(n.flags&1048576)!==0&&pm(n,ho,n.index);switch(n.lanes=0,n.tag){case 16:e:{var o=n.pendingProps;if(t=Rs(n.elementType),n.type=t,typeof t=="function")ku(t)?(o=Ns(t,o),n.tag=1,n=Ng(null,n,t,o,a)):(n.tag=0,n=Uf(null,n,t,o,a));else{if(t!=null){var u=t.$$typeof;if(u===P){n.tag=11,n=bg(null,n,t,o,a);break e}else if(u===z){n.tag=14,n=Tg(null,n,t,o,a);break e}}throw n=fe(t)||t,Error(r(306,n,""))}}return n;case 0:return Uf(t,n,n.type,n.pendingProps,a);case 1:return o=n.type,u=Ns(o,n.pendingProps),Ng(t,n,o,u,a);case 3:e:{if(Ae(n,n.stateNode.containerInfo),t===null)throw Error(r(387));o=n.pendingProps;var h=n.memoizedState;u=h.element,sf(t,n),So(n,o,null,a);var S=n.memoizedState;if(o=S.cache,Ba(n,un,o),o!==h.cache&&Ju(n,[un],a,!0),yo(),o=S.element,h.isDehydrated)if(h={element:o,isDehydrated:!1,cache:S.cache},n.updateQueue.baseState=h,n.memoizedState=h,n.flags&256){n=Ug(t,n,o,a);break e}else if(o!==u){u=ui(Error(r(424)),n),po(u),n=Ug(t,n,o,a);break e}else for(t=n.stateNode.containerInfo,t.nodeType===9?t=t.body:t=t.nodeName==="HTML"?t.ownerDocument.body:t,Xt=mi(t.firstChild),En=n,Et=!0,Ia=null,di=!0,a=Rm(n,null,o,a),n.child=a;a;)a.flags=a.flags&-3|4096,a=a.sibling;else{if(Es(),o===u){n=oa(t,n,a);break e}Tn(t,n,o,a)}n=n.child}return n;case 26:return Jl(t,n),t===null?(a=q_(n.type,null,n.pendingProps,null))?n.memoizedState=a:Et||(a=n.type,t=n.pendingProps,o=mc(ie.current).createElement(a),o[on]=n,o[mn]=t,An(o,a,t),W(o),n.stateNode=o):n.memoizedState=q_(n.type,t.memoizedProps,n.pendingProps,t.memoizedState),null;case 27:return Qe(n),t===null&&Et&&(o=n.stateNode=j_(n.type,n.pendingProps,ie.current),En=n,di=!0,u=Xt,Ja(n.type)?(vh=u,Xt=mi(o.firstChild)):Xt=u),Tn(t,n,n.pendingProps.children,a),Jl(t,n),t===null&&(n.flags|=4194304),n.child;case 5:return t===null&&Et&&((u=o=Xt)&&(o=mS(o,n.type,n.pendingProps,di),o!==null?(n.stateNode=o,En=n,Xt=mi(o.firstChild),di=!1,u=!0):u=!1),u||za(n)),Qe(n),u=n.type,h=n.pendingProps,S=t!==null?t.memoizedProps:null,o=h.children,dh(u,h)?o=null:S!==null&&dh(u,S)&&(n.flags|=32),n.memoizedState!==null&&(u=hf(t,n,Dy,null,null,a),Go._currentValue=u),Jl(t,n),Tn(t,n,o,a),n.child;case 6:return t===null&&Et&&((t=a=Xt)&&(a=gS(a,n.pendingProps,di),a!==null?(n.stateNode=a,En=n,Xt=null,t=!0):t=!1),t||za(n)),null;case 13:return Lg(t,n,a);case 4:return Ae(n,n.stateNode.containerInfo),o=n.pendingProps,t===null?n.child=ws(n,null,o,a):Tn(t,n,o,a),n.child;case 11:return bg(t,n,n.type,n.pendingProps,a);case 7:return Tn(t,n,n.pendingProps,a),n.child;case 8:return Tn(t,n,n.pendingProps.children,a),n.child;case 12:return Tn(t,n,n.pendingProps.children,a),n.child;case 10:return o=n.pendingProps,Ba(n,n.type,o.value),Tn(t,n,o.children,a),n.child;case 9:return u=n.type._context,o=n.pendingProps.children,Ts(n),u=bn(u),o=o(u),n.flags|=1,Tn(t,n,o,a),n.child;case 14:return Tg(t,n,n.type,n.pendingProps,a);case 15:return Ag(t,n,n.type,n.pendingProps,a);case 19:return Pg(t,n,a);case 31:return zy(t,n,a);case 22:return Rg(t,n,a,n.pendingProps);case 24:return Ts(n),o=bn(un),t===null?(u=tf(),u===null&&(u=jt,h=$u(),u.pooledCache=h,h.refCount++,h!==null&&(u.pooledCacheLanes|=a),u=h),n.memoizedState={parent:o,cache:u},af(n),Ba(n,un,u)):((t.lanes&a)!==0&&(sf(t,n),So(n,null,null,a),yo()),u=t.memoizedState,h=n.memoizedState,u.parent!==o?(u={parent:o,cache:o},n.memoizedState=u,n.lanes===0&&(n.memoizedState=n.updateQueue.baseState=u),Ba(n,un,o)):(o=h.cache,Ba(n,un,o),o!==u.cache&&Ju(n,[un],a,!0))),Tn(t,n,n.pendingProps.children,a),n.child;case 29:throw n.pendingProps}throw Error(r(156,n.tag))}function la(t){t.flags|=4}function Hf(t,n,a,o,u){if((n=(t.mode&32)!==0)&&(n=!1),n){if(t.flags|=16777216,(u&335544128)===u)if(t.stateNode.complete)t.flags|=8192;else if(c_())t.flags|=8192;else throw Cs=Il,nf}else t.flags&=-16777217}function Ig(t,n){if(n.type!=="stylesheet"||(n.state.loading&4)!==0)t.flags&=-16777217;else if(t.flags|=16777216,!J_(n))if(c_())t.flags|=8192;else throw Cs=Il,nf}function ec(t,n){n!==null&&(t.flags|=4),t.flags&16384&&(n=t.tag!==22?Ft():536870912,t.lanes|=n,xr|=n)}function Ro(t,n){if(!Et)switch(t.tailMode){case"hidden":n=t.tail;for(var a=null;n!==null;)n.alternate!==null&&(a=n),n=n.sibling;a===null?t.tail=null:a.sibling=null;break;case"collapsed":a=t.tail;for(var o=null;a!==null;)a.alternate!==null&&(o=a),a=a.sibling;o===null?n||t.tail===null?t.tail=null:t.tail.sibling=null:o.sibling=null}}function Wt(t){var n=t.alternate!==null&&t.alternate.child===t.child,a=0,o=0;if(n)for(var u=t.child;u!==null;)a|=u.lanes|u.childLanes,o|=u.subtreeFlags&65011712,o|=u.flags&65011712,u.return=t,u=u.sibling;else for(u=t.child;u!==null;)a|=u.lanes|u.childLanes,o|=u.subtreeFlags,o|=u.flags,u.return=t,u=u.sibling;return t.subtreeFlags|=o,t.childLanes=a,n}function Hy(t,n,a){var o=n.pendingProps;switch(qu(n),n.tag){case 16:case 15:case 0:case 11:case 7:case 8:case 12:case 9:case 14:return Wt(n),null;case 1:return Wt(n),null;case 3:return a=n.stateNode,o=null,t!==null&&(o=t.memoizedState.cache),n.memoizedState.cache!==o&&(n.flags|=2048),aa(un),Ge(),a.pendingContext&&(a.context=a.pendingContext,a.pendingContext=null),(t===null||t.child===null)&&(rr(n)?la(n):t===null||t.memoizedState.isDehydrated&&(n.flags&256)===0||(n.flags|=1024,Zu())),Wt(n),null;case 26:var u=n.type,h=n.memoizedState;return t===null?(la(n),h!==null?(Wt(n),Ig(n,h)):(Wt(n),Hf(n,u,null,o,a))):h?h!==t.memoizedState?(la(n),Wt(n),Ig(n,h)):(Wt(n),n.flags&=-16777217):(t=t.memoizedProps,t!==o&&la(n),Wt(n),Hf(n,u,t,o,a)),null;case 27:if(qe(n),a=ie.current,u=n.type,t!==null&&n.stateNode!=null)t.memoizedProps!==o&&la(n);else{if(!o){if(n.stateNode===null)throw Error(r(166));return Wt(n),null}t=he.current,rr(n)?gm(n):(t=j_(u,o,a),n.stateNode=t,la(n))}return Wt(n),null;case 5:if(qe(n),u=n.type,t!==null&&n.stateNode!=null)t.memoizedProps!==o&&la(n);else{if(!o){if(n.stateNode===null)throw Error(r(166));return Wt(n),null}if(h=he.current,rr(n))gm(n);else{var S=mc(ie.current);switch(h){case 1:h=S.createElementNS("http://www.w3.org/2000/svg",u);break;case 2:h=S.createElementNS("http://www.w3.org/1998/Math/MathML",u);break;default:switch(u){case"svg":h=S.createElementNS("http://www.w3.org/2000/svg",u);break;case"math":h=S.createElementNS("http://www.w3.org/1998/Math/MathML",u);break;case"script":h=S.createElement("div"),h.innerHTML="<script><\/script>",h=h.removeChild(h.firstChild);break;case"select":h=typeof o.is=="string"?S.createElement("select",{is:o.is}):S.createElement("select"),o.multiple?h.multiple=!0:o.size&&(h.size=o.size);break;default:h=typeof o.is=="string"?S.createElement(u,{is:o.is}):S.createElement(u)}}h[on]=n,h[mn]=o;e:for(S=n.child;S!==null;){if(S.tag===5||S.tag===6)h.appendChild(S.stateNode);else if(S.tag!==4&&S.tag!==27&&S.child!==null){S.child.return=S,S=S.child;continue}if(S===n)break e;for(;S.sibling===null;){if(S.return===null||S.return===n)break e;S=S.return}S.sibling.return=S.return,S=S.sibling}n.stateNode=h;e:switch(An(h,u,o),u){case"button":case"input":case"select":case"textarea":o=!!o.autoFocus;break e;case"img":o=!0;break e;default:o=!1}o&&la(n)}}return Wt(n),Hf(n,n.type,t===null?null:t.memoizedProps,n.pendingProps,a),null;case 6:if(t&&n.stateNode!=null)t.memoizedProps!==o&&la(n);else{if(typeof o!="string"&&n.stateNode===null)throw Error(r(166));if(t=ie.current,rr(n)){if(t=n.stateNode,a=n.memoizedProps,o=null,u=En,u!==null)switch(u.tag){case 27:case 5:o=u.memoizedProps}t[on]=n,t=!!(t.nodeValue===a||o!==null&&o.suppressHydrationWarning===!0||L_(t.nodeValue,a)),t||za(n,!0)}else t=mc(t).createTextNode(o),t[on]=n,n.stateNode=t}return Wt(n),null;case 31:if(a=n.memoizedState,t===null||t.memoizedState!==null){if(o=rr(n),a!==null){if(t===null){if(!o)throw Error(r(318));if(t=n.memoizedState,t=t!==null?t.dehydrated:null,!t)throw Error(r(557));t[on]=n}else Es(),(n.flags&128)===0&&(n.memoizedState=null),n.flags|=4;Wt(n),t=!1}else a=Zu(),t!==null&&t.memoizedState!==null&&(t.memoizedState.hydrationErrors=a),t=!0;if(!t)return n.flags&256?(ni(n),n):(ni(n),null);if((n.flags&128)!==0)throw Error(r(558))}return Wt(n),null;case 13:if(o=n.memoizedState,t===null||t.memoizedState!==null&&t.memoizedState.dehydrated!==null){if(u=rr(n),o!==null&&o.dehydrated!==null){if(t===null){if(!u)throw Error(r(318));if(u=n.memoizedState,u=u!==null?u.dehydrated:null,!u)throw Error(r(317));u[on]=n}else Es(),(n.flags&128)===0&&(n.memoizedState=null),n.flags|=4;Wt(n),u=!1}else u=Zu(),t!==null&&t.memoizedState!==null&&(t.memoizedState.hydrationErrors=u),u=!0;if(!u)return n.flags&256?(ni(n),n):(ni(n),null)}return ni(n),(n.flags&128)!==0?(n.lanes=a,n):(a=o!==null,t=t!==null&&t.memoizedState!==null,a&&(o=n.child,u=null,o.alternate!==null&&o.alternate.memoizedState!==null&&o.alternate.memoizedState.cachePool!==null&&(u=o.alternate.memoizedState.cachePool.pool),h=null,o.memoizedState!==null&&o.memoizedState.cachePool!==null&&(h=o.memoizedState.cachePool.pool),h!==u&&(o.flags|=2048)),a!==t&&a&&(n.child.flags|=8192),ec(n,n.updateQueue),Wt(n),null);case 4:return Ge(),t===null&&lh(n.stateNode.containerInfo),Wt(n),null;case 10:return aa(n.type),Wt(n),null;case 19:if(j(an),o=n.memoizedState,o===null)return Wt(n),null;if(u=(n.flags&128)!==0,h=o.rendering,h===null)if(u)Ro(o,!1);else{if(tn!==0||t!==null&&(t.flags&128)!==0)for(t=n.child;t!==null;){if(h=Gl(t),h!==null){for(n.flags|=128,Ro(o,!1),t=h.updateQueue,n.updateQueue=t,ec(n,t),n.subtreeFlags=0,t=a,a=n.child;a!==null;)fm(a,t),a=a.sibling;return ve(an,an.current&1|2),Et&&na(n,o.treeForkCount),n.child}t=t.sibling}o.tail!==null&&b()>sc&&(n.flags|=128,u=!0,Ro(o,!1),n.lanes=4194304)}else{if(!u)if(t=Gl(h),t!==null){if(n.flags|=128,u=!0,t=t.updateQueue,n.updateQueue=t,ec(n,t),Ro(o,!0),o.tail===null&&o.tailMode==="hidden"&&!h.alternate&&!Et)return Wt(n),null}else 2*b()-o.renderingStartTime>sc&&a!==536870912&&(n.flags|=128,u=!0,Ro(o,!1),n.lanes=4194304);o.isBackwards?(h.sibling=n.child,n.child=h):(t=o.last,t!==null?t.sibling=h:n.child=h,o.last=h)}return o.tail!==null?(t=o.tail,o.rendering=t,o.tail=t.sibling,o.renderingStartTime=b(),t.sibling=null,a=an.current,ve(an,u?a&1|2:a&1),Et&&na(n,o.treeForkCount),t):(Wt(n),null);case 22:case 23:return ni(n),cf(),o=n.memoizedState!==null,t!==null?t.memoizedState!==null!==o&&(n.flags|=8192):o&&(n.flags|=8192),o?(a&536870912)!==0&&(n.flags&128)===0&&(Wt(n),n.subtreeFlags&6&&(n.flags|=8192)):Wt(n),a=n.updateQueue,a!==null&&ec(n,a.retryQueue),a=null,t!==null&&t.memoizedState!==null&&t.memoizedState.cachePool!==null&&(a=t.memoizedState.cachePool.pool),o=null,n.memoizedState!==null&&n.memoizedState.cachePool!==null&&(o=n.memoizedState.cachePool.pool),o!==a&&(n.flags|=2048),t!==null&&j(As),null;case 24:return a=null,t!==null&&(a=t.memoizedState.cache),n.memoizedState.cache!==a&&(n.flags|=2048),aa(un),Wt(n),null;case 25:return null;case 30:return null}throw Error(r(156,n.tag))}function Gy(t,n){switch(qu(n),n.tag){case 1:return t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 3:return aa(un),Ge(),t=n.flags,(t&65536)!==0&&(t&128)===0?(n.flags=t&-65537|128,n):null;case 26:case 27:case 5:return qe(n),null;case 31:if(n.memoizedState!==null){if(ni(n),n.alternate===null)throw Error(r(340));Es()}return t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 13:if(ni(n),t=n.memoizedState,t!==null&&t.dehydrated!==null){if(n.alternate===null)throw Error(r(340));Es()}return t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 19:return j(an),null;case 4:return Ge(),null;case 10:return aa(n.type),null;case 22:case 23:return ni(n),cf(),t!==null&&j(As),t=n.flags,t&65536?(n.flags=t&-65537|128,n):null;case 24:return aa(un),null;case 25:return null;default:return null}}function zg(t,n){switch(qu(n),n.tag){case 3:aa(un),Ge();break;case 26:case 27:case 5:qe(n);break;case 4:Ge();break;case 31:n.memoizedState!==null&&ni(n);break;case 13:ni(n);break;case 19:j(an);break;case 10:aa(n.type);break;case 22:case 23:ni(n),cf(),t!==null&&j(As);break;case 24:aa(un)}}function Co(t,n){try{var a=n.updateQueue,o=a!==null?a.lastEffect:null;if(o!==null){var u=o.next;a=u;do{if((a.tag&t)===t){o=void 0;var h=a.create,S=a.inst;o=h(),S.destroy=o}a=a.next}while(a!==u)}}catch(D){zt(n,n.return,D)}}function Xa(t,n,a){try{var o=n.updateQueue,u=o!==null?o.lastEffect:null;if(u!==null){var h=u.next;o=h;do{if((o.tag&t)===t){var S=o.inst,D=S.destroy;if(D!==void 0){S.destroy=void 0,u=n;var G=a,ae=D;try{ae()}catch(_e){zt(u,G,_e)}}}o=o.next}while(o!==h)}}catch(_e){zt(n,n.return,_e)}}function Bg(t){var n=t.updateQueue;if(n!==null){var a=t.stateNode;try{wm(n,a)}catch(o){zt(t,t.return,o)}}}function Hg(t,n,a){a.props=Ns(t.type,t.memoizedProps),a.state=t.memoizedState;try{a.componentWillUnmount()}catch(o){zt(t,n,o)}}function wo(t,n){try{var a=t.ref;if(a!==null){switch(t.tag){case 26:case 27:case 5:var o=t.stateNode;break;case 30:o=t.stateNode;break;default:o=t.stateNode}typeof a=="function"?t.refCleanup=a(o):a.current=o}}catch(u){zt(t,n,u)}}function Hi(t,n){var a=t.ref,o=t.refCleanup;if(a!==null)if(typeof o=="function")try{o()}catch(u){zt(t,n,u)}finally{t.refCleanup=null,t=t.alternate,t!=null&&(t.refCleanup=null)}else if(typeof a=="function")try{a(null)}catch(u){zt(t,n,u)}else a.current=null}function Gg(t){var n=t.type,a=t.memoizedProps,o=t.stateNode;try{e:switch(n){case"button":case"input":case"select":case"textarea":a.autoFocus&&o.focus();break e;case"img":a.src?o.src=a.src:a.srcSet&&(o.srcset=a.srcSet)}}catch(u){zt(t,t.return,u)}}function Gf(t,n,a){try{var o=t.stateNode;cS(o,t.type,a,n),o[mn]=n}catch(u){zt(t,t.return,u)}}function Vg(t){return t.tag===5||t.tag===3||t.tag===26||t.tag===27&&Ja(t.type)||t.tag===4}function Vf(t){e:for(;;){for(;t.sibling===null;){if(t.return===null||Vg(t.return))return null;t=t.return}for(t.sibling.return=t.return,t=t.sibling;t.tag!==5&&t.tag!==6&&t.tag!==18;){if(t.tag===27&&Ja(t.type)||t.flags&2||t.child===null||t.tag===4)continue e;t.child.return=t,t=t.child}if(!(t.flags&2))return t.stateNode}}function kf(t,n,a){var o=t.tag;if(o===5||o===6)t=t.stateNode,n?(a.nodeType===9?a.body:a.nodeName==="HTML"?a.ownerDocument.body:a).insertBefore(t,n):(n=a.nodeType===9?a.body:a.nodeName==="HTML"?a.ownerDocument.body:a,n.appendChild(t),a=a._reactRootContainer,a!=null||n.onclick!==null||(n.onclick=$i));else if(o!==4&&(o===27&&Ja(t.type)&&(a=t.stateNode,n=null),t=t.child,t!==null))for(kf(t,n,a),t=t.sibling;t!==null;)kf(t,n,a),t=t.sibling}function tc(t,n,a){var o=t.tag;if(o===5||o===6)t=t.stateNode,n?a.insertBefore(t,n):a.appendChild(t);else if(o!==4&&(o===27&&Ja(t.type)&&(a=t.stateNode),t=t.child,t!==null))for(tc(t,n,a),t=t.sibling;t!==null;)tc(t,n,a),t=t.sibling}function kg(t){var n=t.stateNode,a=t.memoizedProps;try{for(var o=t.type,u=n.attributes;u.length;)n.removeAttributeNode(u[0]);An(n,o,a),n[on]=t,n[mn]=a}catch(h){zt(t,t.return,h)}}var ca=!1,dn=!1,jf=!1,jg=typeof WeakSet=="function"?WeakSet:Set,Sn=null;function Vy(t,n){if(t=t.containerInfo,fh=Mc,t=nm(t),Fu(t)){if("selectionStart"in t)var a={start:t.selectionStart,end:t.selectionEnd};else e:{a=(a=t.ownerDocument)&&a.defaultView||window;var o=a.getSelection&&a.getSelection();if(o&&o.rangeCount!==0){a=o.anchorNode;var u=o.anchorOffset,h=o.focusNode;o=o.focusOffset;try{a.nodeType,h.nodeType}catch{a=null;break e}var S=0,D=-1,G=-1,ae=0,_e=0,Me=t,le=null;t:for(;;){for(var ue;Me!==a||u!==0&&Me.nodeType!==3||(D=S+u),Me!==h||o!==0&&Me.nodeType!==3||(G=S+o),Me.nodeType===3&&(S+=Me.nodeValue.length),(ue=Me.firstChild)!==null;)le=Me,Me=ue;for(;;){if(Me===t)break t;if(le===a&&++ae===u&&(D=S),le===h&&++_e===o&&(G=S),(ue=Me.nextSibling)!==null)break;Me=le,le=Me.parentNode}Me=ue}a=D===-1||G===-1?null:{start:D,end:G}}else a=null}a=a||{start:0,end:0}}else a=null;for(hh={focusedElem:t,selectionRange:a},Mc=!1,Sn=n;Sn!==null;)if(n=Sn,t=n.child,(n.subtreeFlags&1028)!==0&&t!==null)t.return=n,Sn=t;else for(;Sn!==null;){switch(n=Sn,h=n.alternate,t=n.flags,n.tag){case 0:if((t&4)!==0&&(t=n.updateQueue,t=t!==null?t.events:null,t!==null))for(a=0;a<t.length;a++)u=t[a],u.ref.impl=u.nextImpl;break;case 11:case 15:break;case 1:if((t&1024)!==0&&h!==null){t=void 0,a=n,u=h.memoizedProps,h=h.memoizedState,o=a.stateNode;try{var ke=Ns(a.type,u);t=o.getSnapshotBeforeUpdate(ke,h),o.__reactInternalSnapshotBeforeUpdate=t}catch(et){zt(a,a.return,et)}}break;case 3:if((t&1024)!==0){if(t=n.stateNode.containerInfo,a=t.nodeType,a===9)mh(t);else if(a===1)switch(t.nodeName){case"HEAD":case"HTML":case"BODY":mh(t);break;default:t.textContent=""}}break;case 5:case 26:case 27:case 6:case 4:case 17:break;default:if((t&1024)!==0)throw Error(r(163))}if(t=n.sibling,t!==null){t.return=n.return,Sn=t;break}Sn=n.return}}function Xg(t,n,a){var o=a.flags;switch(a.tag){case 0:case 11:case 15:fa(t,a),o&4&&Co(5,a);break;case 1:if(fa(t,a),o&4)if(t=a.stateNode,n===null)try{t.componentDidMount()}catch(S){zt(a,a.return,S)}else{var u=Ns(a.type,n.memoizedProps);n=n.memoizedState;try{t.componentDidUpdate(u,n,t.__reactInternalSnapshotBeforeUpdate)}catch(S){zt(a,a.return,S)}}o&64&&Bg(a),o&512&&wo(a,a.return);break;case 3:if(fa(t,a),o&64&&(t=a.updateQueue,t!==null)){if(n=null,a.child!==null)switch(a.child.tag){case 27:case 5:n=a.child.stateNode;break;case 1:n=a.child.stateNode}try{wm(t,n)}catch(S){zt(a,a.return,S)}}break;case 27:n===null&&o&4&&kg(a);case 26:case 5:fa(t,a),n===null&&o&4&&Gg(a),o&512&&wo(a,a.return);break;case 12:fa(t,a);break;case 31:fa(t,a),o&4&&Yg(t,a);break;case 13:fa(t,a),o&4&&Zg(t,a),o&64&&(t=a.memoizedState,t!==null&&(t=t.dehydrated,t!==null&&(a=Qy.bind(null,a),_S(t,a))));break;case 22:if(o=a.memoizedState!==null||ca,!o){n=n!==null&&n.memoizedState!==null||dn,u=ca;var h=dn;ca=o,(dn=n)&&!h?ha(t,a,(a.subtreeFlags&8772)!==0):fa(t,a),ca=u,dn=h}break;case 30:break;default:fa(t,a)}}function Wg(t){var n=t.alternate;n!==null&&(t.alternate=null,Wg(n)),t.child=null,t.deletions=null,t.sibling=null,t.tag===5&&(n=t.stateNode,n!==null&&no(n)),t.stateNode=null,t.return=null,t.dependencies=null,t.memoizedProps=null,t.memoizedState=null,t.pendingProps=null,t.stateNode=null,t.updateQueue=null}var Kt=null,Gn=!1;function ua(t,n,a){for(a=a.child;a!==null;)qg(t,n,a),a=a.sibling}function qg(t,n,a){if(be&&typeof be.onCommitFiberUnmount=="function")try{be.onCommitFiberUnmount(Re,a)}catch{}switch(a.tag){case 26:dn||Hi(a,n),ua(t,n,a),a.memoizedState?a.memoizedState.count--:a.stateNode&&(a=a.stateNode,a.parentNode.removeChild(a));break;case 27:dn||Hi(a,n);var o=Kt,u=Gn;Ja(a.type)&&(Kt=a.stateNode,Gn=!1),ua(t,n,a),zo(a.stateNode),Kt=o,Gn=u;break;case 5:dn||Hi(a,n);case 6:if(o=Kt,u=Gn,Kt=null,ua(t,n,a),Kt=o,Gn=u,Kt!==null)if(Gn)try{(Kt.nodeType===9?Kt.body:Kt.nodeName==="HTML"?Kt.ownerDocument.body:Kt).removeChild(a.stateNode)}catch(h){zt(a,n,h)}else try{Kt.removeChild(a.stateNode)}catch(h){zt(a,n,h)}break;case 18:Kt!==null&&(Gn?(t=Kt,B_(t.nodeType===9?t.body:t.nodeName==="HTML"?t.ownerDocument.body:t,a.stateNode),Rr(t)):B_(Kt,a.stateNode));break;case 4:o=Kt,u=Gn,Kt=a.stateNode.containerInfo,Gn=!0,ua(t,n,a),Kt=o,Gn=u;break;case 0:case 11:case 14:case 15:Xa(2,a,n),dn||Xa(4,a,n),ua(t,n,a);break;case 1:dn||(Hi(a,n),o=a.stateNode,typeof o.componentWillUnmount=="function"&&Hg(a,n,o)),ua(t,n,a);break;case 21:ua(t,n,a);break;case 22:dn=(o=dn)||a.memoizedState!==null,ua(t,n,a),dn=o;break;default:ua(t,n,a)}}function Yg(t,n){if(n.memoizedState===null&&(t=n.alternate,t!==null&&(t=t.memoizedState,t!==null))){t=t.dehydrated;try{Rr(t)}catch(a){zt(n,n.return,a)}}}function Zg(t,n){if(n.memoizedState===null&&(t=n.alternate,t!==null&&(t=t.memoizedState,t!==null&&(t=t.dehydrated,t!==null))))try{Rr(t)}catch(a){zt(n,n.return,a)}}function ky(t){switch(t.tag){case 31:case 13:case 19:var n=t.stateNode;return n===null&&(n=t.stateNode=new jg),n;case 22:return t=t.stateNode,n=t._retryCache,n===null&&(n=t._retryCache=new jg),n;default:throw Error(r(435,t.tag))}}function nc(t,n){var a=ky(t);n.forEach(function(o){if(!a.has(o)){a.add(o);var u=Jy.bind(null,t,o);o.then(u,u)}})}function Vn(t,n){var a=n.deletions;if(a!==null)for(var o=0;o<a.length;o++){var u=a[o],h=t,S=n,D=S;e:for(;D!==null;){switch(D.tag){case 27:if(Ja(D.type)){Kt=D.stateNode,Gn=!1;break e}break;case 5:Kt=D.stateNode,Gn=!1;break e;case 3:case 4:Kt=D.stateNode.containerInfo,Gn=!0;break e}D=D.return}if(Kt===null)throw Error(r(160));qg(h,S,u),Kt=null,Gn=!1,h=u.alternate,h!==null&&(h.return=null),u.return=null}if(n.subtreeFlags&13886)for(n=n.child;n!==null;)Kg(n,t),n=n.sibling}var Ri=null;function Kg(t,n){var a=t.alternate,o=t.flags;switch(t.tag){case 0:case 11:case 14:case 15:Vn(n,t),kn(t),o&4&&(Xa(3,t,t.return),Co(3,t),Xa(5,t,t.return));break;case 1:Vn(n,t),kn(t),o&512&&(dn||a===null||Hi(a,a.return)),o&64&&ca&&(t=t.updateQueue,t!==null&&(o=t.callbacks,o!==null&&(a=t.shared.hiddenCallbacks,t.shared.hiddenCallbacks=a===null?o:a.concat(o))));break;case 26:var u=Ri;if(Vn(n,t),kn(t),o&512&&(dn||a===null||Hi(a,a.return)),o&4){var h=a!==null?a.memoizedState:null;if(o=t.memoizedState,a===null)if(o===null)if(t.stateNode===null){e:{o=t.type,a=t.memoizedProps,u=u.ownerDocument||u;t:switch(o){case"title":h=u.getElementsByTagName("title")[0],(!h||h[gs]||h[on]||h.namespaceURI==="http://www.w3.org/2000/svg"||h.hasAttribute("itemprop"))&&(h=u.createElement(o),u.head.insertBefore(h,u.querySelector("head > title"))),An(h,o,a),h[on]=t,W(h),o=h;break e;case"link":var S=K_("link","href",u).get(o+(a.href||""));if(S){for(var D=0;D<S.length;D++)if(h=S[D],h.getAttribute("href")===(a.href==null||a.href===""?null:a.href)&&h.getAttribute("rel")===(a.rel==null?null:a.rel)&&h.getAttribute("title")===(a.title==null?null:a.title)&&h.getAttribute("crossorigin")===(a.crossOrigin==null?null:a.crossOrigin)){S.splice(D,1);break t}}h=u.createElement(o),An(h,o,a),u.head.appendChild(h);break;case"meta":if(S=K_("meta","content",u).get(o+(a.content||""))){for(D=0;D<S.length;D++)if(h=S[D],h.getAttribute("content")===(a.content==null?null:""+a.content)&&h.getAttribute("name")===(a.name==null?null:a.name)&&h.getAttribute("property")===(a.property==null?null:a.property)&&h.getAttribute("http-equiv")===(a.httpEquiv==null?null:a.httpEquiv)&&h.getAttribute("charset")===(a.charSet==null?null:a.charSet)){S.splice(D,1);break t}}h=u.createElement(o),An(h,o,a),u.head.appendChild(h);break;default:throw Error(r(468,o))}h[on]=t,W(h),o=h}t.stateNode=o}else Q_(u,t.type,t.stateNode);else t.stateNode=Z_(u,o,t.memoizedProps);else h!==o?(h===null?a.stateNode!==null&&(a=a.stateNode,a.parentNode.removeChild(a)):h.count--,o===null?Q_(u,t.type,t.stateNode):Z_(u,o,t.memoizedProps)):o===null&&t.stateNode!==null&&Gf(t,t.memoizedProps,a.memoizedProps)}break;case 27:Vn(n,t),kn(t),o&512&&(dn||a===null||Hi(a,a.return)),a!==null&&o&4&&Gf(t,t.memoizedProps,a.memoizedProps);break;case 5:if(Vn(n,t),kn(t),o&512&&(dn||a===null||Hi(a,a.return)),t.flags&32){u=t.stateNode;try{Fn(u,"")}catch(ke){zt(t,t.return,ke)}}o&4&&t.stateNode!=null&&(u=t.memoizedProps,Gf(t,u,a!==null?a.memoizedProps:u)),o&1024&&(jf=!0);break;case 6:if(Vn(n,t),kn(t),o&4){if(t.stateNode===null)throw Error(r(162));o=t.memoizedProps,a=t.stateNode;try{a.nodeValue=o}catch(ke){zt(t,t.return,ke)}}break;case 3:if(vc=null,u=Ri,Ri=gc(n.containerInfo),Vn(n,t),Ri=u,kn(t),o&4&&a!==null&&a.memoizedState.isDehydrated)try{Rr(n.containerInfo)}catch(ke){zt(t,t.return,ke)}jf&&(jf=!1,Qg(t));break;case 4:o=Ri,Ri=gc(t.stateNode.containerInfo),Vn(n,t),kn(t),Ri=o;break;case 12:Vn(n,t),kn(t);break;case 31:Vn(n,t),kn(t),o&4&&(o=t.updateQueue,o!==null&&(t.updateQueue=null,nc(t,o)));break;case 13:Vn(n,t),kn(t),t.child.flags&8192&&t.memoizedState!==null!=(a!==null&&a.memoizedState!==null)&&(ac=b()),o&4&&(o=t.updateQueue,o!==null&&(t.updateQueue=null,nc(t,o)));break;case 22:u=t.memoizedState!==null;var G=a!==null&&a.memoizedState!==null,ae=ca,_e=dn;if(ca=ae||u,dn=_e||G,Vn(n,t),dn=_e,ca=ae,kn(t),o&8192)e:for(n=t.stateNode,n._visibility=u?n._visibility&-2:n._visibility|1,u&&(a===null||G||ca||dn||Us(t)),a=null,n=t;;){if(n.tag===5||n.tag===26){if(a===null){G=a=n;try{if(h=G.stateNode,u)S=h.style,typeof S.setProperty=="function"?S.setProperty("display","none","important"):S.display="none";else{D=G.stateNode;var Me=G.memoizedProps.style,le=Me!=null&&Me.hasOwnProperty("display")?Me.display:null;D.style.display=le==null||typeof le=="boolean"?"":(""+le).trim()}}catch(ke){zt(G,G.return,ke)}}}else if(n.tag===6){if(a===null){G=n;try{G.stateNode.nodeValue=u?"":G.memoizedProps}catch(ke){zt(G,G.return,ke)}}}else if(n.tag===18){if(a===null){G=n;try{var ue=G.stateNode;u?H_(ue,!0):H_(G.stateNode,!1)}catch(ke){zt(G,G.return,ke)}}}else if((n.tag!==22&&n.tag!==23||n.memoizedState===null||n===t)&&n.child!==null){n.child.return=n,n=n.child;continue}if(n===t)break e;for(;n.sibling===null;){if(n.return===null||n.return===t)break e;a===n&&(a=null),n=n.return}a===n&&(a=null),n.sibling.return=n.return,n=n.sibling}o&4&&(o=t.updateQueue,o!==null&&(a=o.retryQueue,a!==null&&(o.retryQueue=null,nc(t,a))));break;case 19:Vn(n,t),kn(t),o&4&&(o=t.updateQueue,o!==null&&(t.updateQueue=null,nc(t,o)));break;case 30:break;case 21:break;default:Vn(n,t),kn(t)}}function kn(t){var n=t.flags;if(n&2){try{for(var a,o=t.return;o!==null;){if(Vg(o)){a=o;break}o=o.return}if(a==null)throw Error(r(160));switch(a.tag){case 27:var u=a.stateNode,h=Vf(t);tc(t,h,u);break;case 5:var S=a.stateNode;a.flags&32&&(Fn(S,""),a.flags&=-33);var D=Vf(t);tc(t,D,S);break;case 3:case 4:var G=a.stateNode.containerInfo,ae=Vf(t);kf(t,ae,G);break;default:throw Error(r(161))}}catch(_e){zt(t,t.return,_e)}t.flags&=-3}n&4096&&(t.flags&=-4097)}function Qg(t){if(t.subtreeFlags&1024)for(t=t.child;t!==null;){var n=t;Qg(n),n.tag===5&&n.flags&1024&&n.stateNode.reset(),t=t.sibling}}function fa(t,n){if(n.subtreeFlags&8772)for(n=n.child;n!==null;)Xg(t,n.alternate,n),n=n.sibling}function Us(t){for(t=t.child;t!==null;){var n=t;switch(n.tag){case 0:case 11:case 14:case 15:Xa(4,n,n.return),Us(n);break;case 1:Hi(n,n.return);var a=n.stateNode;typeof a.componentWillUnmount=="function"&&Hg(n,n.return,a),Us(n);break;case 27:zo(n.stateNode);case 26:case 5:Hi(n,n.return),Us(n);break;case 22:n.memoizedState===null&&Us(n);break;case 30:Us(n);break;default:Us(n)}t=t.sibling}}function ha(t,n,a){for(a=a&&(n.subtreeFlags&8772)!==0,n=n.child;n!==null;){var o=n.alternate,u=t,h=n,S=h.flags;switch(h.tag){case 0:case 11:case 15:ha(u,h,a),Co(4,h);break;case 1:if(ha(u,h,a),o=h,u=o.stateNode,typeof u.componentDidMount=="function")try{u.componentDidMount()}catch(ae){zt(o,o.return,ae)}if(o=h,u=o.updateQueue,u!==null){var D=o.stateNode;try{var G=u.shared.hiddenCallbacks;if(G!==null)for(u.shared.hiddenCallbacks=null,u=0;u<G.length;u++)Cm(G[u],D)}catch(ae){zt(o,o.return,ae)}}a&&S&64&&Bg(h),wo(h,h.return);break;case 27:kg(h);case 26:case 5:ha(u,h,a),a&&o===null&&S&4&&Gg(h),wo(h,h.return);break;case 12:ha(u,h,a);break;case 31:ha(u,h,a),a&&S&4&&Yg(u,h);break;case 13:ha(u,h,a),a&&S&4&&Zg(u,h);break;case 22:h.memoizedState===null&&ha(u,h,a),wo(h,h.return);break;case 30:break;default:ha(u,h,a)}n=n.sibling}}function Xf(t,n){var a=null;t!==null&&t.memoizedState!==null&&t.memoizedState.cachePool!==null&&(a=t.memoizedState.cachePool.pool),t=null,n.memoizedState!==null&&n.memoizedState.cachePool!==null&&(t=n.memoizedState.cachePool.pool),t!==a&&(t!=null&&t.refCount++,a!=null&&mo(a))}function Wf(t,n){t=null,n.alternate!==null&&(t=n.alternate.memoizedState.cache),n=n.memoizedState.cache,n!==t&&(n.refCount++,t!=null&&mo(t))}function Ci(t,n,a,o){if(n.subtreeFlags&10256)for(n=n.child;n!==null;)Jg(t,n,a,o),n=n.sibling}function Jg(t,n,a,o){var u=n.flags;switch(n.tag){case 0:case 11:case 15:Ci(t,n,a,o),u&2048&&Co(9,n);break;case 1:Ci(t,n,a,o);break;case 3:Ci(t,n,a,o),u&2048&&(t=null,n.alternate!==null&&(t=n.alternate.memoizedState.cache),n=n.memoizedState.cache,n!==t&&(n.refCount++,t!=null&&mo(t)));break;case 12:if(u&2048){Ci(t,n,a,o),t=n.stateNode;try{var h=n.memoizedProps,S=h.id,D=h.onPostCommit;typeof D=="function"&&D(S,n.alternate===null?"mount":"update",t.passiveEffectDuration,-0)}catch(G){zt(n,n.return,G)}}else Ci(t,n,a,o);break;case 31:Ci(t,n,a,o);break;case 13:Ci(t,n,a,o);break;case 23:break;case 22:h=n.stateNode,S=n.alternate,n.memoizedState!==null?h._visibility&2?Ci(t,n,a,o):Do(t,n):h._visibility&2?Ci(t,n,a,o):(h._visibility|=2,gr(t,n,a,o,(n.subtreeFlags&10256)!==0||!1)),u&2048&&Xf(S,n);break;case 24:Ci(t,n,a,o),u&2048&&Wf(n.alternate,n);break;default:Ci(t,n,a,o)}}function gr(t,n,a,o,u){for(u=u&&((n.subtreeFlags&10256)!==0||!1),n=n.child;n!==null;){var h=t,S=n,D=a,G=o,ae=S.flags;switch(S.tag){case 0:case 11:case 15:gr(h,S,D,G,u),Co(8,S);break;case 23:break;case 22:var _e=S.stateNode;S.memoizedState!==null?_e._visibility&2?gr(h,S,D,G,u):Do(h,S):(_e._visibility|=2,gr(h,S,D,G,u)),u&&ae&2048&&Xf(S.alternate,S);break;case 24:gr(h,S,D,G,u),u&&ae&2048&&Wf(S.alternate,S);break;default:gr(h,S,D,G,u)}n=n.sibling}}function Do(t,n){if(n.subtreeFlags&10256)for(n=n.child;n!==null;){var a=t,o=n,u=o.flags;switch(o.tag){case 22:Do(a,o),u&2048&&Xf(o.alternate,o);break;case 24:Do(a,o),u&2048&&Wf(o.alternate,o);break;default:Do(a,o)}n=n.sibling}}var No=8192;function _r(t,n,a){if(t.subtreeFlags&No)for(t=t.child;t!==null;)$g(t,n,a),t=t.sibling}function $g(t,n,a){switch(t.tag){case 26:_r(t,n,a),t.flags&No&&t.memoizedState!==null&&wS(a,Ri,t.memoizedState,t.memoizedProps);break;case 5:_r(t,n,a);break;case 3:case 4:var o=Ri;Ri=gc(t.stateNode.containerInfo),_r(t,n,a),Ri=o;break;case 22:t.memoizedState===null&&(o=t.alternate,o!==null&&o.memoizedState!==null?(o=No,No=16777216,_r(t,n,a),No=o):_r(t,n,a));break;default:_r(t,n,a)}}function e_(t){var n=t.alternate;if(n!==null&&(t=n.child,t!==null)){n.child=null;do n=t.sibling,t.sibling=null,t=n;while(t!==null)}}function Uo(t){var n=t.deletions;if((t.flags&16)!==0){if(n!==null)for(var a=0;a<n.length;a++){var o=n[a];Sn=o,n_(o,t)}e_(t)}if(t.subtreeFlags&10256)for(t=t.child;t!==null;)t_(t),t=t.sibling}function t_(t){switch(t.tag){case 0:case 11:case 15:Uo(t),t.flags&2048&&Xa(9,t,t.return);break;case 3:Uo(t);break;case 12:Uo(t);break;case 22:var n=t.stateNode;t.memoizedState!==null&&n._visibility&2&&(t.return===null||t.return.tag!==13)?(n._visibility&=-3,ic(t)):Uo(t);break;default:Uo(t)}}function ic(t){var n=t.deletions;if((t.flags&16)!==0){if(n!==null)for(var a=0;a<n.length;a++){var o=n[a];Sn=o,n_(o,t)}e_(t)}for(t=t.child;t!==null;){switch(n=t,n.tag){case 0:case 11:case 15:Xa(8,n,n.return),ic(n);break;case 22:a=n.stateNode,a._visibility&2&&(a._visibility&=-3,ic(n));break;default:ic(n)}t=t.sibling}}function n_(t,n){for(;Sn!==null;){var a=Sn;switch(a.tag){case 0:case 11:case 15:Xa(8,a,n);break;case 23:case 22:if(a.memoizedState!==null&&a.memoizedState.cachePool!==null){var o=a.memoizedState.cachePool.pool;o!=null&&o.refCount++}break;case 24:mo(a.memoizedState.cache)}if(o=a.child,o!==null)o.return=a,Sn=o;else e:for(a=t;Sn!==null;){o=Sn;var u=o.sibling,h=o.return;if(Wg(o),o===a){Sn=null;break e}if(u!==null){u.return=h,Sn=u;break e}Sn=h}}}var jy={getCacheForType:function(t){var n=bn(un),a=n.data.get(t);return a===void 0&&(a=t(),n.data.set(t,a)),a},cacheSignal:function(){return bn(un).controller.signal}},Xy=typeof WeakMap=="function"?WeakMap:Map,Ut=0,jt=null,_t=null,St=0,It=0,ii=null,Wa=!1,vr=!1,qf=!1,da=0,tn=0,qa=0,Ls=0,Yf=0,ai=0,xr=0,Lo=null,jn=null,Zf=!1,ac=0,i_=0,sc=1/0,rc=null,Ya=null,_n=0,Za=null,yr=null,pa=0,Kf=0,Qf=null,a_=null,Oo=0,Jf=null;function si(){return(Ut&2)!==0&&St!==0?St&-St:I.T!==null?ah():Ii()}function s_(){if(ai===0)if((St&536870912)===0||Et){var t=Ce;Ce<<=1,(Ce&3932160)===0&&(Ce=262144),ai=t}else ai=536870912;return t=ti.current,t!==null&&(t.flags|=32),ai}function Xn(t,n,a){(t===jt&&(It===2||It===9)||t.cancelPendingCommit!==null)&&(Sr(t,0),Ka(t,St,ai,!1)),Ln(t,a),((Ut&2)===0||t!==jt)&&(t===jt&&((Ut&2)===0&&(Ls|=a),tn===4&&Ka(t,St,ai,!1)),Gi(t))}function r_(t,n,a){if((Ut&6)!==0)throw Error(r(327));var o=!a&&(n&127)===0&&(n&t.expiredLanes)===0||He(t,n),u=o?Yy(t,n):eh(t,n,!0),h=o;do{if(u===0){vr&&!o&&Ka(t,n,0,!1);break}else{if(a=t.current.alternate,h&&!Wy(a)){u=eh(t,n,!1),h=!1;continue}if(u===2){if(h=n,t.errorRecoveryDisabledLanes&h)var S=0;else S=t.pendingLanes&-536870913,S=S!==0?S:S&536870912?536870912:0;if(S!==0){n=S;e:{var D=t;u=Lo;var G=D.current.memoizedState.isDehydrated;if(G&&(Sr(D,S).flags|=256),S=eh(D,S,!1),S!==2){if(qf&&!G){D.errorRecoveryDisabledLanes|=h,Ls|=h,u=4;break e}h=jn,jn=u,h!==null&&(jn===null?jn=h:jn.push.apply(jn,h))}u=S}if(h=!1,u!==2)continue}}if(u===1){Sr(t,0),Ka(t,n,0,!0);break}e:{switch(o=t,h=u,h){case 0:case 1:throw Error(r(345));case 4:if((n&4194048)!==n)break;case 6:Ka(o,n,ai,!Wa);break e;case 2:jn=null;break;case 3:case 5:break;default:throw Error(r(329))}if((n&62914560)===n&&(u=ac+300-b(),10<u)){if(Ka(o,n,ai,!Wa),me(o,0,!0)!==0)break e;pa=n,o.timeoutHandle=I_(o_.bind(null,o,a,jn,rc,Zf,n,ai,Ls,xr,Wa,h,"Throttled",-0,0),u);break e}o_(o,a,jn,rc,Zf,n,ai,Ls,xr,Wa,h,null,-0,0)}}break}while(!0);Gi(t)}function o_(t,n,a,o,u,h,S,D,G,ae,_e,Me,le,ue){if(t.timeoutHandle=-1,Me=n.subtreeFlags,Me&8192||(Me&16785408)===16785408){Me={stylesheets:null,count:0,imgCount:0,imgBytes:0,suspenseyImages:[],waitingForImages:!0,waitingForViewTransition:!1,unsuspend:$i},$g(n,h,Me);var ke=(h&62914560)===h?ac-b():(h&4194048)===h?i_-b():0;if(ke=DS(Me,ke),ke!==null){pa=h,t.cancelPendingCommit=ke(m_.bind(null,t,n,h,a,o,u,S,D,G,_e,Me,null,le,ue)),Ka(t,h,S,!ae);return}}m_(t,n,h,a,o,u,S,D,G)}function Wy(t){for(var n=t;;){var a=n.tag;if((a===0||a===11||a===15)&&n.flags&16384&&(a=n.updateQueue,a!==null&&(a=a.stores,a!==null)))for(var o=0;o<a.length;o++){var u=a[o],h=u.getSnapshot;u=u.value;try{if(!$n(h(),u))return!1}catch{return!1}}if(a=n.child,n.subtreeFlags&16384&&a!==null)a.return=n,n=a;else{if(n===t)break;for(;n.sibling===null;){if(n.return===null||n.return===t)return!0;n=n.return}n.sibling.return=n.return,n=n.sibling}}return!0}function Ka(t,n,a,o){n&=~Yf,n&=~Ls,t.suspendedLanes|=n,t.pingedLanes&=~n,o&&(t.warmLanes|=n),o=t.expirationTimes;for(var u=n;0<u;){var h=31-Pe(u),S=1<<h;o[h]=-1,u&=~S}a!==0&&to(t,a,n)}function oc(){return(Ut&6)===0?(Po(0),!1):!0}function $f(){if(_t!==null){if(It===0)var t=_t.return;else t=_t,ia=bs=null,mf(t),fr=null,_o=0,t=_t;for(;t!==null;)zg(t.alternate,t),t=t.return;_t=null}}function Sr(t,n){var a=t.timeoutHandle;a!==-1&&(t.timeoutHandle=-1,hS(a)),a=t.cancelPendingCommit,a!==null&&(t.cancelPendingCommit=null,a()),pa=0,$f(),jt=t,_t=a=ta(t.current,null),St=n,It=0,ii=null,Wa=!1,vr=He(t,n),qf=!1,xr=ai=Yf=Ls=qa=tn=0,jn=Lo=null,Zf=!1,(n&8)!==0&&(n|=n&32);var o=t.entangledLanes;if(o!==0)for(t=t.entanglements,o&=n;0<o;){var u=31-Pe(o),h=1<<u;n|=t[u],o&=~h}return da=n,Cl(),a}function l_(t,n){ct=null,I.H=To,n===ur||n===Fl?(n=bm(),It=3):n===nf?(n=bm(),It=4):It=n===Nf?8:n!==null&&typeof n=="object"&&typeof n.then=="function"?6:1,ii=n,_t===null&&(tn=1,Kl(t,ui(n,t.current)))}function c_(){var t=ti.current;return t===null?!0:(St&4194048)===St?pi===null:(St&62914560)===St||(St&536870912)!==0?t===pi:!1}function u_(){var t=I.H;return I.H=To,t===null?To:t}function f_(){var t=I.A;return I.A=jy,t}function lc(){tn=4,Wa||(St&4194048)!==St&&ti.current!==null||(vr=!0),(qa&134217727)===0&&(Ls&134217727)===0||jt===null||Ka(jt,St,ai,!1)}function eh(t,n,a){var o=Ut;Ut|=2;var u=u_(),h=f_();(jt!==t||St!==n)&&(rc=null,Sr(t,n)),n=!1;var S=tn;e:do try{if(It!==0&&_t!==null){var D=_t,G=ii;switch(It){case 8:$f(),S=6;break e;case 3:case 2:case 9:case 6:ti.current===null&&(n=!0);var ae=It;if(It=0,ii=null,Mr(t,D,G,ae),a&&vr){S=0;break e}break;default:ae=It,It=0,ii=null,Mr(t,D,G,ae)}}qy(),S=tn;break}catch(_e){l_(t,_e)}while(!0);return n&&t.shellSuspendCounter++,ia=bs=null,Ut=o,I.H=u,I.A=h,_t===null&&(jt=null,St=0,Cl()),S}function qy(){for(;_t!==null;)h_(_t)}function Yy(t,n){var a=Ut;Ut|=2;var o=u_(),u=f_();jt!==t||St!==n?(rc=null,sc=b()+500,Sr(t,n)):vr=He(t,n);e:do try{if(It!==0&&_t!==null){n=_t;var h=ii;t:switch(It){case 1:It=0,ii=null,Mr(t,n,h,1);break;case 2:case 9:if(Mm(h)){It=0,ii=null,d_(n);break}n=function(){It!==2&&It!==9||jt!==t||(It=7),Gi(t)},h.then(n,n);break e;case 3:It=7;break e;case 4:It=5;break e;case 7:Mm(h)?(It=0,ii=null,d_(n)):(It=0,ii=null,Mr(t,n,h,7));break;case 5:var S=null;switch(_t.tag){case 26:S=_t.memoizedState;case 5:case 27:var D=_t;if(S?J_(S):D.stateNode.complete){It=0,ii=null;var G=D.sibling;if(G!==null)_t=G;else{var ae=D.return;ae!==null?(_t=ae,cc(ae)):_t=null}break t}}It=0,ii=null,Mr(t,n,h,5);break;case 6:It=0,ii=null,Mr(t,n,h,6);break;case 8:$f(),tn=6;break e;default:throw Error(r(462))}}Zy();break}catch(_e){l_(t,_e)}while(!0);return ia=bs=null,I.H=o,I.A=u,Ut=a,_t!==null?0:(jt=null,St=0,Cl(),tn)}function Zy(){for(;_t!==null&&!Ye();)h_(_t)}function h_(t){var n=Fg(t.alternate,t,da);t.memoizedProps=t.pendingProps,n===null?cc(t):_t=n}function d_(t){var n=t,a=n.alternate;switch(n.tag){case 15:case 0:n=Dg(a,n,n.pendingProps,n.type,void 0,St);break;case 11:n=Dg(a,n,n.pendingProps,n.type.render,n.ref,St);break;case 5:mf(n);default:zg(a,n),n=_t=fm(n,da),n=Fg(a,n,da)}t.memoizedProps=t.pendingProps,n===null?cc(t):_t=n}function Mr(t,n,a,o){ia=bs=null,mf(n),fr=null,_o=0;var u=n.return;try{if(Iy(t,u,n,a,St)){tn=1,Kl(t,ui(a,t.current)),_t=null;return}}catch(h){if(u!==null)throw _t=u,h;tn=1,Kl(t,ui(a,t.current)),_t=null;return}n.flags&32768?(Et||o===1?t=!0:vr||(St&536870912)!==0?t=!1:(Wa=t=!0,(o===2||o===9||o===3||o===6)&&(o=ti.current,o!==null&&o.tag===13&&(o.flags|=16384))),p_(n,t)):cc(n)}function cc(t){var n=t;do{if((n.flags&32768)!==0){p_(n,Wa);return}t=n.return;var a=Hy(n.alternate,n,da);if(a!==null){_t=a;return}if(n=n.sibling,n!==null){_t=n;return}_t=n=t}while(n!==null);tn===0&&(tn=5)}function p_(t,n){do{var a=Gy(t.alternate,t);if(a!==null){a.flags&=32767,_t=a;return}if(a=t.return,a!==null&&(a.flags|=32768,a.subtreeFlags=0,a.deletions=null),!n&&(t=t.sibling,t!==null)){_t=t;return}_t=t=a}while(t!==null);tn=6,_t=null}function m_(t,n,a,o,u,h,S,D,G){t.cancelPendingCommit=null;do uc();while(_n!==0);if((Ut&6)!==0)throw Error(r(327));if(n!==null){if(n===t.current)throw Error(r(177));if(h=n.lanes|n.childLanes,h|=Gu,Mi(t,a,h,S,D,G),t===jt&&(_t=jt=null,St=0),yr=n,Za=t,pa=a,Kf=h,Qf=u,a_=o,(n.subtreeFlags&10256)!==0||(n.flags&10256)!==0?(t.callbackNode=null,t.callbackPriority=0,$y(ge,function(){return y_(),null})):(t.callbackNode=null,t.callbackPriority=0),o=(n.flags&13878)!==0,(n.subtreeFlags&13878)!==0||o){o=I.T,I.T=null,u=B.p,B.p=2,S=Ut,Ut|=4;try{Vy(t,n,a)}finally{Ut=S,B.p=u,I.T=o}}_n=1,g_(),__(),v_()}}function g_(){if(_n===1){_n=0;var t=Za,n=yr,a=(n.flags&13878)!==0;if((n.subtreeFlags&13878)!==0||a){a=I.T,I.T=null;var o=B.p;B.p=2;var u=Ut;Ut|=4;try{Kg(n,t);var h=hh,S=nm(t.containerInfo),D=h.focusedElem,G=h.selectionRange;if(S!==D&&D&&D.ownerDocument&&tm(D.ownerDocument.documentElement,D)){if(G!==null&&Fu(D)){var ae=G.start,_e=G.end;if(_e===void 0&&(_e=ae),"selectionStart"in D)D.selectionStart=ae,D.selectionEnd=Math.min(_e,D.value.length);else{var Me=D.ownerDocument||document,le=Me&&Me.defaultView||window;if(le.getSelection){var ue=le.getSelection(),ke=D.textContent.length,et=Math.min(G.start,ke),Vt=G.end===void 0?et:Math.min(G.end,ke);!ue.extend&&et>Vt&&(S=Vt,Vt=et,et=S);var J=em(D,et),X=em(D,Vt);if(J&&X&&(ue.rangeCount!==1||ue.anchorNode!==J.node||ue.anchorOffset!==J.offset||ue.focusNode!==X.node||ue.focusOffset!==X.offset)){var ne=Me.createRange();ne.setStart(J.node,J.offset),ue.removeAllRanges(),et>Vt?(ue.addRange(ne),ue.extend(X.node,X.offset)):(ne.setEnd(X.node,X.offset),ue.addRange(ne))}}}}for(Me=[],ue=D;ue=ue.parentNode;)ue.nodeType===1&&Me.push({element:ue,left:ue.scrollLeft,top:ue.scrollTop});for(typeof D.focus=="function"&&D.focus(),D=0;D<Me.length;D++){var ye=Me[D];ye.element.scrollLeft=ye.left,ye.element.scrollTop=ye.top}}Mc=!!fh,hh=fh=null}finally{Ut=u,B.p=o,I.T=a}}t.current=n,_n=2}}function __(){if(_n===2){_n=0;var t=Za,n=yr,a=(n.flags&8772)!==0;if((n.subtreeFlags&8772)!==0||a){a=I.T,I.T=null;var o=B.p;B.p=2;var u=Ut;Ut|=4;try{Xg(t,n.alternate,n)}finally{Ut=u,B.p=o,I.T=a}}_n=3}}function v_(){if(_n===4||_n===3){_n=0,F();var t=Za,n=yr,a=pa,o=a_;(n.subtreeFlags&10256)!==0||(n.flags&10256)!==0?_n=5:(_n=0,yr=Za=null,x_(t,t.pendingLanes));var u=t.pendingLanes;if(u===0&&(Ya=null),Ys(a),n=n.stateNode,be&&typeof be.onCommitFiberRoot=="function")try{be.onCommitFiberRoot(Re,n,void 0,(n.current.flags&128)===128)}catch{}if(o!==null){n=I.T,u=B.p,B.p=2,I.T=null;try{for(var h=t.onRecoverableError,S=0;S<o.length;S++){var D=o[S];h(D.value,{componentStack:D.stack})}}finally{I.T=n,B.p=u}}(pa&3)!==0&&uc(),Gi(t),u=t.pendingLanes,(a&261930)!==0&&(u&42)!==0?t===Jf?Oo++:(Oo=0,Jf=t):Oo=0,Po(0)}}function x_(t,n){(t.pooledCacheLanes&=n)===0&&(n=t.pooledCache,n!=null&&(t.pooledCache=null,mo(n)))}function uc(){return g_(),__(),v_(),y_()}function y_(){if(_n!==5)return!1;var t=Za,n=Kf;Kf=0;var a=Ys(pa),o=I.T,u=B.p;try{B.p=32>a?32:a,I.T=null,a=Qf,Qf=null;var h=Za,S=pa;if(_n=0,yr=Za=null,pa=0,(Ut&6)!==0)throw Error(r(331));var D=Ut;if(Ut|=4,t_(h.current),Jg(h,h.current,S,a),Ut=D,Po(0,!1),be&&typeof be.onPostCommitFiberRoot=="function")try{be.onPostCommitFiberRoot(Re,h)}catch{}return!0}finally{B.p=u,I.T=o,x_(t,n)}}function S_(t,n,a){n=ui(a,n),n=Df(t.stateNode,n,2),t=Va(t,n,2),t!==null&&(Ln(t,2),Gi(t))}function zt(t,n,a){if(t.tag===3)S_(t,t,a);else for(;n!==null;){if(n.tag===3){S_(n,t,a);break}else if(n.tag===1){var o=n.stateNode;if(typeof n.type.getDerivedStateFromError=="function"||typeof o.componentDidCatch=="function"&&(Ya===null||!Ya.has(o))){t=ui(a,t),a=Mg(2),o=Va(n,a,2),o!==null&&(Eg(a,o,n,t),Ln(o,2),Gi(o));break}}n=n.return}}function th(t,n,a){var o=t.pingCache;if(o===null){o=t.pingCache=new Xy;var u=new Set;o.set(n,u)}else u=o.get(n),u===void 0&&(u=new Set,o.set(n,u));u.has(a)||(qf=!0,u.add(a),t=Ky.bind(null,t,n,a),n.then(t,t))}function Ky(t,n,a){var o=t.pingCache;o!==null&&o.delete(n),t.pingedLanes|=t.suspendedLanes&a,t.warmLanes&=~a,jt===t&&(St&a)===a&&(tn===4||tn===3&&(St&62914560)===St&&300>b()-ac?(Ut&2)===0&&Sr(t,0):Yf|=a,xr===St&&(xr=0)),Gi(t)}function M_(t,n){n===0&&(n=Ft()),t=Ss(t,n),t!==null&&(Ln(t,n),Gi(t))}function Qy(t){var n=t.memoizedState,a=0;n!==null&&(a=n.retryLane),M_(t,a)}function Jy(t,n){var a=0;switch(t.tag){case 31:case 13:var o=t.stateNode,u=t.memoizedState;u!==null&&(a=u.retryLane);break;case 19:o=t.stateNode;break;case 22:o=t.stateNode._retryCache;break;default:throw Error(r(314))}o!==null&&o.delete(n),M_(t,a)}function $y(t,n){return bt(t,n)}var fc=null,Er=null,nh=!1,hc=!1,ih=!1,Qa=0;function Gi(t){t!==Er&&t.next===null&&(Er===null?fc=Er=t:Er=Er.next=t),hc=!0,nh||(nh=!0,tS())}function Po(t,n){if(!ih&&hc){ih=!0;do for(var a=!1,o=fc;o!==null;){if(t!==0){var u=o.pendingLanes;if(u===0)var h=0;else{var S=o.suspendedLanes,D=o.pingedLanes;h=(1<<31-Pe(42|t)+1)-1,h&=u&~(S&~D),h=h&201326741?h&201326741|1:h?h|2:0}h!==0&&(a=!0,A_(o,h))}else h=St,h=me(o,o===jt?h:0,o.cancelPendingCommit!==null||o.timeoutHandle!==-1),(h&3)===0||He(o,h)||(a=!0,A_(o,h));o=o.next}while(a);ih=!1}}function eS(){E_()}function E_(){hc=nh=!1;var t=0;Qa!==0&&fS()&&(t=Qa);for(var n=b(),a=null,o=fc;o!==null;){var u=o.next,h=b_(o,n);h===0?(o.next=null,a===null?fc=u:a.next=u,u===null&&(Er=a)):(a=o,(t!==0||(h&3)!==0)&&(hc=!0)),o=u}_n!==0&&_n!==5||Po(t),Qa!==0&&(Qa=0)}function b_(t,n){for(var a=t.suspendedLanes,o=t.pingedLanes,u=t.expirationTimes,h=t.pendingLanes&-62914561;0<h;){var S=31-Pe(h),D=1<<S,G=u[S];G===-1?((D&a)===0||(D&o)!==0)&&(u[S]=it(D,n)):G<=n&&(t.expiredLanes|=D),h&=~D}if(n=jt,a=St,a=me(t,t===n?a:0,t.cancelPendingCommit!==null||t.timeoutHandle!==-1),o=t.callbackNode,a===0||t===n&&(It===2||It===9)||t.cancelPendingCommit!==null)return o!==null&&o!==null&&Ot(o),t.callbackNode=null,t.callbackPriority=0;if((a&3)===0||He(t,a)){if(n=a&-a,n===t.callbackPriority)return n;switch(o!==null&&Ot(o),Ys(a)){case 2:case 8:a=Ee;break;case 32:a=ge;break;case 268435456:a=De;break;default:a=ge}return o=T_.bind(null,t),a=bt(a,o),t.callbackPriority=n,t.callbackNode=a,n}return o!==null&&o!==null&&Ot(o),t.callbackPriority=2,t.callbackNode=null,2}function T_(t,n){if(_n!==0&&_n!==5)return t.callbackNode=null,t.callbackPriority=0,null;var a=t.callbackNode;if(uc()&&t.callbackNode!==a)return null;var o=St;return o=me(t,t===jt?o:0,t.cancelPendingCommit!==null||t.timeoutHandle!==-1),o===0?null:(r_(t,o,n),b_(t,b()),t.callbackNode!=null&&t.callbackNode===a?T_.bind(null,t):null)}function A_(t,n){if(uc())return null;r_(t,n,!0)}function tS(){dS(function(){(Ut&6)!==0?bt(xe,eS):E_()})}function ah(){if(Qa===0){var t=lr;t===0&&(t=we,we<<=1,(we&261888)===0&&(we=256)),Qa=t}return Qa}function R_(t){return t==null||typeof t=="symbol"||typeof t=="boolean"?null:typeof t=="function"?t:yl(""+t)}function C_(t,n){var a=n.ownerDocument.createElement("input");return a.name=n.name,a.value=n.value,t.id&&a.setAttribute("form",t.id),n.parentNode.insertBefore(a,n),t=new FormData(t),a.parentNode.removeChild(a),t}function nS(t,n,a,o,u){if(n==="submit"&&a&&a.stateNode===u){var h=R_((u[mn]||null).action),S=o.submitter;S&&(n=(n=S[mn]||null)?R_(n.formAction):S.getAttribute("formAction"),n!==null&&(h=n,S=null));var D=new bl("action","action",null,o,u);t.push({event:D,listeners:[{instance:null,listener:function(){if(o.defaultPrevented){if(Qa!==0){var G=S?C_(u,S):new FormData(u);bf(a,{pending:!0,data:G,method:u.method,action:h},null,G)}}else typeof h=="function"&&(D.preventDefault(),G=S?C_(u,S):new FormData(u),bf(a,{pending:!0,data:G,method:u.method,action:h},h,G))},currentTarget:u}]})}}for(var sh=0;sh<Hu.length;sh++){var rh=Hu[sh],iS=rh.toLowerCase(),aS=rh[0].toUpperCase()+rh.slice(1);Ai(iS,"on"+aS)}Ai(sm,"onAnimationEnd"),Ai(rm,"onAnimationIteration"),Ai(om,"onAnimationStart"),Ai("dblclick","onDoubleClick"),Ai("focusin","onFocus"),Ai("focusout","onBlur"),Ai(yy,"onTransitionRun"),Ai(Sy,"onTransitionStart"),Ai(My,"onTransitionCancel"),Ai(lm,"onTransitionEnd"),Ue("onMouseEnter",["mouseout","mouseover"]),Ue("onMouseLeave",["mouseout","mouseover"]),Ue("onPointerEnter",["pointerout","pointerover"]),Ue("onPointerLeave",["pointerout","pointerover"]),te("onChange","change click focusin focusout input keydown keyup selectionchange".split(" ")),te("onSelect","focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")),te("onBeforeInput",["compositionend","keypress","textInput","paste"]),te("onCompositionEnd","compositionend focusout keydown keypress keyup mousedown".split(" ")),te("onCompositionStart","compositionstart focusout keydown keypress keyup mousedown".split(" ")),te("onCompositionUpdate","compositionupdate focusout keydown keypress keyup mousedown".split(" "));var Fo="abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "),sS=new Set("beforetoggle cancel close invalid load scroll scrollend toggle".split(" ").concat(Fo));function w_(t,n){n=(n&4)!==0;for(var a=0;a<t.length;a++){var o=t[a],u=o.event;o=o.listeners;e:{var h=void 0;if(n)for(var S=o.length-1;0<=S;S--){var D=o[S],G=D.instance,ae=D.currentTarget;if(D=D.listener,G!==h&&u.isPropagationStopped())break e;h=D,u.currentTarget=ae;try{h(u)}catch(_e){Rl(_e)}u.currentTarget=null,h=G}else for(S=0;S<o.length;S++){if(D=o[S],G=D.instance,ae=D.currentTarget,D=D.listener,G!==h&&u.isPropagationStopped())break e;h=D,u.currentTarget=ae;try{h(u)}catch(_e){Rl(_e)}u.currentTarget=null,h=G}}}}function vt(t,n){var a=n[Ua];a===void 0&&(a=n[Ua]=new Set);var o=t+"__bubble";a.has(o)||(D_(n,t,2,!1),a.add(o))}function oh(t,n,a){var o=0;n&&(o|=4),D_(a,t,o,n)}var dc="_reactListening"+Math.random().toString(36).slice(2);function lh(t){if(!t[dc]){t[dc]=!0,ce.forEach(function(a){a!=="selectionchange"&&(sS.has(a)||oh(a,!1,t),oh(a,!0,t))});var n=t.nodeType===9?t:t.ownerDocument;n===null||n[dc]||(n[dc]=!0,oh("selectionchange",!1,n))}}function D_(t,n,a,o){switch(s0(n)){case 2:var u=LS;break;case 8:u=OS;break;default:u=Eh}a=u.bind(null,n,a,t),u=void 0,!Ru||n!=="touchstart"&&n!=="touchmove"&&n!=="wheel"||(u=!0),o?u!==void 0?t.addEventListener(n,a,{capture:!0,passive:u}):t.addEventListener(n,a,!0):u!==void 0?t.addEventListener(n,a,{passive:u}):t.addEventListener(n,a,!1)}function ch(t,n,a,o,u){var h=o;if((n&1)===0&&(n&2)===0&&o!==null)e:for(;;){if(o===null)return;var S=o.tag;if(S===3||S===4){var D=o.stateNode.containerInfo;if(D===u)break;if(S===4)for(S=o.return;S!==null;){var G=S.tag;if((G===3||G===4)&&S.stateNode.containerInfo===u)return;S=S.return}for(;D!==null;){if(S=La(D),S===null)return;if(G=S.tag,G===5||G===6||G===26||G===27){o=h=S;continue e}D=D.parentNode}}o=o.return}Pp(function(){var ae=h,_e=Tu(a),Me=[];e:{var le=cm.get(t);if(le!==void 0){var ue=bl,ke=t;switch(t){case"keypress":if(Ml(a)===0)break e;case"keydown":case"keyup":ue=Jx;break;case"focusin":ke="focus",ue=Nu;break;case"focusout":ke="blur",ue=Nu;break;case"beforeblur":case"afterblur":ue=Nu;break;case"click":if(a.button===2)break e;case"auxclick":case"dblclick":case"mousedown":case"mousemove":case"mouseup":case"mouseout":case"mouseover":case"contextmenu":ue=zp;break;case"drag":case"dragend":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"dragstart":case"drop":ue=Hx;break;case"touchcancel":case"touchend":case"touchmove":case"touchstart":ue=ty;break;case sm:case rm:case om:ue=kx;break;case lm:ue=iy;break;case"scroll":case"scrollend":ue=zx;break;case"wheel":ue=sy;break;case"copy":case"cut":case"paste":ue=Xx;break;case"gotpointercapture":case"lostpointercapture":case"pointercancel":case"pointerdown":case"pointermove":case"pointerout":case"pointerover":case"pointerup":ue=Hp;break;case"toggle":case"beforetoggle":ue=oy}var et=(n&4)!==0,Vt=!et&&(t==="scroll"||t==="scrollend"),J=et?le!==null?le+"Capture":null:le;et=[];for(var X=ae,ne;X!==null;){var ye=X;if(ne=ye.stateNode,ye=ye.tag,ye!==5&&ye!==26&&ye!==27||ne===null||J===null||(ye=io(X,J),ye!=null&&et.push(Io(X,ye,ne))),Vt)break;X=X.return}0<et.length&&(le=new ue(le,ke,null,a,_e),Me.push({event:le,listeners:et}))}}if((n&7)===0){e:{if(le=t==="mouseover"||t==="pointerover",ue=t==="mouseout"||t==="pointerout",le&&a!==bu&&(ke=a.relatedTarget||a.fromElement)&&(La(ke)||ke[Qi]))break e;if((ue||le)&&(le=_e.window===_e?_e:(le=_e.ownerDocument)?le.defaultView||le.parentWindow:window,ue?(ke=a.relatedTarget||a.toElement,ue=ae,ke=ke?La(ke):null,ke!==null&&(Vt=c(ke),et=ke.tag,ke!==Vt||et!==5&&et!==27&&et!==6)&&(ke=null)):(ue=null,ke=ae),ue!==ke)){if(et=zp,ye="onMouseLeave",J="onMouseEnter",X="mouse",(t==="pointerout"||t==="pointerover")&&(et=Hp,ye="onPointerLeave",J="onPointerEnter",X="pointer"),Vt=ue==null?le:_s(ue),ne=ke==null?le:_s(ke),le=new et(ye,X+"leave",ue,a,_e),le.target=Vt,le.relatedTarget=ne,ye=null,La(_e)===ae&&(et=new et(J,X+"enter",ke,a,_e),et.target=ne,et.relatedTarget=Vt,ye=et),Vt=ye,ue&&ke)t:{for(et=rS,J=ue,X=ke,ne=0,ye=J;ye;ye=et(ye))ne++;ye=0;for(var $e=X;$e;$e=et($e))ye++;for(;0<ne-ye;)J=et(J),ne--;for(;0<ye-ne;)X=et(X),ye--;for(;ne--;){if(J===X||X!==null&&J===X.alternate){et=J;break t}J=et(J),X=et(X)}et=null}else et=null;ue!==null&&N_(Me,le,ue,et,!1),ke!==null&&Vt!==null&&N_(Me,Vt,ke,et,!0)}}e:{if(le=ae?_s(ae):window,ue=le.nodeName&&le.nodeName.toLowerCase(),ue==="select"||ue==="input"&&le.type==="file")var wt=Yp;else if(Wp(le))if(Zp)wt=_y;else{wt=my;var Ze=py}else ue=le.nodeName,!ue||ue.toLowerCase()!=="input"||le.type!=="checkbox"&&le.type!=="radio"?ae&&Ks(ae.elementType)&&(wt=Yp):wt=gy;if(wt&&(wt=wt(t,ae))){qp(Me,wt,a,_e);break e}Ze&&Ze(t,le,ae),t==="focusout"&&ae&&le.type==="number"&&ae.memoizedProps.value!=null&&bi(le,"number",le.value)}switch(Ze=ae?_s(ae):window,t){case"focusin":(Wp(Ze)||Ze.contentEditable==="true")&&(er=Ze,Iu=ae,fo=null);break;case"focusout":fo=Iu=er=null;break;case"mousedown":zu=!0;break;case"contextmenu":case"mouseup":case"dragend":zu=!1,im(Me,a,_e);break;case"selectionchange":if(xy)break;case"keydown":case"keyup":im(Me,a,_e)}var ht;if(Lu)e:{switch(t){case"compositionstart":var Mt="onCompositionStart";break e;case"compositionend":Mt="onCompositionEnd";break e;case"compositionupdate":Mt="onCompositionUpdate";break e}Mt=void 0}else $s?jp(t,a)&&(Mt="onCompositionEnd"):t==="keydown"&&a.keyCode===229&&(Mt="onCompositionStart");Mt&&(Gp&&a.locale!=="ko"&&($s||Mt!=="onCompositionStart"?Mt==="onCompositionEnd"&&$s&&(ht=Fp()):(Pa=_e,Cu="value"in Pa?Pa.value:Pa.textContent,$s=!0)),Ze=pc(ae,Mt),0<Ze.length&&(Mt=new Bp(Mt,t,null,a,_e),Me.push({event:Mt,listeners:Ze}),ht?Mt.data=ht:(ht=Xp(a),ht!==null&&(Mt.data=ht)))),(ht=cy?uy(t,a):fy(t,a))&&(Mt=pc(ae,"onBeforeInput"),0<Mt.length&&(Ze=new Bp("onBeforeInput","beforeinput",null,a,_e),Me.push({event:Ze,listeners:Mt}),Ze.data=ht)),nS(Me,t,ae,a,_e)}w_(Me,n)})}function Io(t,n,a){return{instance:t,listener:n,currentTarget:a}}function pc(t,n){for(var a=n+"Capture",o=[];t!==null;){var u=t,h=u.stateNode;if(u=u.tag,u!==5&&u!==26&&u!==27||h===null||(u=io(t,a),u!=null&&o.unshift(Io(t,u,h)),u=io(t,n),u!=null&&o.push(Io(t,u,h))),t.tag===3)return o;t=t.return}return[]}function rS(t){if(t===null)return null;do t=t.return;while(t&&t.tag!==5&&t.tag!==27);return t||null}function N_(t,n,a,o,u){for(var h=n._reactName,S=[];a!==null&&a!==o;){var D=a,G=D.alternate,ae=D.stateNode;if(D=D.tag,G!==null&&G===o)break;D!==5&&D!==26&&D!==27||ae===null||(G=ae,u?(ae=io(a,h),ae!=null&&S.unshift(Io(a,ae,G))):u||(ae=io(a,h),ae!=null&&S.push(Io(a,ae,G)))),a=a.return}S.length!==0&&t.push({event:n,listeners:S})}var oS=/\r\n?/g,lS=/\u0000|\uFFFD/g;function U_(t){return(typeof t=="string"?t:""+t).replace(oS,`
`).replace(lS,"")}function L_(t,n){return n=U_(n),U_(t)===n}function Gt(t,n,a,o,u,h){switch(a){case"children":typeof o=="string"?n==="body"||n==="textarea"&&o===""||Fn(t,o):(typeof o=="number"||typeof o=="bigint")&&n!=="body"&&Fn(t,""+o);break;case"className":rt(t,"class",o);break;case"tabIndex":rt(t,"tabindex",o);break;case"dir":case"role":case"viewBox":case"width":case"height":rt(t,a,o);break;case"style":Ji(t,o,h);break;case"data":if(n!=="object"){rt(t,"data",o);break}case"src":case"href":if(o===""&&(n!=="a"||a!=="href")){t.removeAttribute(a);break}if(o==null||typeof o=="function"||typeof o=="symbol"||typeof o=="boolean"){t.removeAttribute(a);break}o=yl(""+o),t.setAttribute(a,o);break;case"action":case"formAction":if(typeof o=="function"){t.setAttribute(a,"javascript:throw new Error('A React form was unexpectedly submitted. If you called form.submit() manually, consider using form.requestSubmit() instead. If you\\'re trying to use event.stopPropagation() in a submit event handler, consider also calling event.preventDefault().')");break}else typeof h=="function"&&(a==="formAction"?(n!=="input"&&Gt(t,n,"name",u.name,u,null),Gt(t,n,"formEncType",u.formEncType,u,null),Gt(t,n,"formMethod",u.formMethod,u,null),Gt(t,n,"formTarget",u.formTarget,u,null)):(Gt(t,n,"encType",u.encType,u,null),Gt(t,n,"method",u.method,u,null),Gt(t,n,"target",u.target,u,null)));if(o==null||typeof o=="symbol"||typeof o=="boolean"){t.removeAttribute(a);break}o=yl(""+o),t.setAttribute(a,o);break;case"onClick":o!=null&&(t.onclick=$i);break;case"onScroll":o!=null&&vt("scroll",t);break;case"onScrollEnd":o!=null&&vt("scrollend",t);break;case"dangerouslySetInnerHTML":if(o!=null){if(typeof o!="object"||!("__html"in o))throw Error(r(61));if(a=o.__html,a!=null){if(u.children!=null)throw Error(r(60));t.innerHTML=a}}break;case"multiple":t.multiple=o&&typeof o!="function"&&typeof o!="symbol";break;case"muted":t.muted=o&&typeof o!="function"&&typeof o!="symbol";break;case"suppressContentEditableWarning":case"suppressHydrationWarning":case"defaultValue":case"defaultChecked":case"innerHTML":case"ref":break;case"autoFocus":break;case"xlinkHref":if(o==null||typeof o=="function"||typeof o=="boolean"||typeof o=="symbol"){t.removeAttribute("xlink:href");break}a=yl(""+o),t.setAttributeNS("http://www.w3.org/1999/xlink","xlink:href",a);break;case"contentEditable":case"spellCheck":case"draggable":case"value":case"autoReverse":case"externalResourcesRequired":case"focusable":case"preserveAlpha":o!=null&&typeof o!="function"&&typeof o!="symbol"?t.setAttribute(a,""+o):t.removeAttribute(a);break;case"inert":case"allowFullScreen":case"async":case"autoPlay":case"controls":case"default":case"defer":case"disabled":case"disablePictureInPicture":case"disableRemotePlayback":case"formNoValidate":case"hidden":case"loop":case"noModule":case"noValidate":case"open":case"playsInline":case"readOnly":case"required":case"reversed":case"scoped":case"seamless":case"itemScope":o&&typeof o!="function"&&typeof o!="symbol"?t.setAttribute(a,""):t.removeAttribute(a);break;case"capture":case"download":o===!0?t.setAttribute(a,""):o!==!1&&o!=null&&typeof o!="function"&&typeof o!="symbol"?t.setAttribute(a,o):t.removeAttribute(a);break;case"cols":case"rows":case"size":case"span":o!=null&&typeof o!="function"&&typeof o!="symbol"&&!isNaN(o)&&1<=o?t.setAttribute(a,o):t.removeAttribute(a);break;case"rowSpan":case"start":o==null||typeof o=="function"||typeof o=="symbol"||isNaN(o)?t.removeAttribute(a):t.setAttribute(a,o);break;case"popover":vt("beforetoggle",t),vt("toggle",t),nt(t,"popover",o);break;case"xlinkActuate":Ve(t,"http://www.w3.org/1999/xlink","xlink:actuate",o);break;case"xlinkArcrole":Ve(t,"http://www.w3.org/1999/xlink","xlink:arcrole",o);break;case"xlinkRole":Ve(t,"http://www.w3.org/1999/xlink","xlink:role",o);break;case"xlinkShow":Ve(t,"http://www.w3.org/1999/xlink","xlink:show",o);break;case"xlinkTitle":Ve(t,"http://www.w3.org/1999/xlink","xlink:title",o);break;case"xlinkType":Ve(t,"http://www.w3.org/1999/xlink","xlink:type",o);break;case"xmlBase":Ve(t,"http://www.w3.org/XML/1998/namespace","xml:base",o);break;case"xmlLang":Ve(t,"http://www.w3.org/XML/1998/namespace","xml:lang",o);break;case"xmlSpace":Ve(t,"http://www.w3.org/XML/1998/namespace","xml:space",o);break;case"is":nt(t,"is",o);break;case"innerText":case"textContent":break;default:(!(2<a.length)||a[0]!=="o"&&a[0]!=="O"||a[1]!=="n"&&a[1]!=="N")&&(a=Fx.get(a)||a,nt(t,a,o))}}function uh(t,n,a,o,u,h){switch(a){case"style":Ji(t,o,h);break;case"dangerouslySetInnerHTML":if(o!=null){if(typeof o!="object"||!("__html"in o))throw Error(r(61));if(a=o.__html,a!=null){if(u.children!=null)throw Error(r(60));t.innerHTML=a}}break;case"children":typeof o=="string"?Fn(t,o):(typeof o=="number"||typeof o=="bigint")&&Fn(t,""+o);break;case"onScroll":o!=null&&vt("scroll",t);break;case"onScrollEnd":o!=null&&vt("scrollend",t);break;case"onClick":o!=null&&(t.onclick=$i);break;case"suppressContentEditableWarning":case"suppressHydrationWarning":case"innerHTML":case"ref":break;case"innerText":case"textContent":break;default:if(!oe.hasOwnProperty(a))e:{if(a[0]==="o"&&a[1]==="n"&&(u=a.endsWith("Capture"),n=a.slice(2,u?a.length-7:void 0),h=t[mn]||null,h=h!=null?h[a]:null,typeof h=="function"&&t.removeEventListener(n,h,u),typeof o=="function")){typeof h!="function"&&h!==null&&(a in t?t[a]=null:t.hasAttribute(a)&&t.removeAttribute(a)),t.addEventListener(n,o,u);break e}a in t?t[a]=o:o===!0?t.setAttribute(a,""):nt(t,a,o)}}}function An(t,n,a){switch(n){case"div":case"span":case"svg":case"path":case"a":case"g":case"p":case"li":break;case"img":vt("error",t),vt("load",t);var o=!1,u=!1,h;for(h in a)if(a.hasOwnProperty(h)){var S=a[h];if(S!=null)switch(h){case"src":o=!0;break;case"srcSet":u=!0;break;case"children":case"dangerouslySetInnerHTML":throw Error(r(137,n));default:Gt(t,n,h,S,a,null)}}u&&Gt(t,n,"srcSet",a.srcSet,a,null),o&&Gt(t,n,"src",a.src,a,null);return;case"input":vt("invalid",t);var D=h=S=u=null,G=null,ae=null;for(o in a)if(a.hasOwnProperty(o)){var _e=a[o];if(_e!=null)switch(o){case"name":u=_e;break;case"type":S=_e;break;case"checked":G=_e;break;case"defaultChecked":ae=_e;break;case"value":h=_e;break;case"defaultValue":D=_e;break;case"children":case"dangerouslySetInnerHTML":if(_e!=null)throw Error(r(137,n));break;default:Gt(t,n,o,_e,a,null)}}Qn(t,h,D,G,ae,S,u,!1);return;case"select":vt("invalid",t),o=S=h=null;for(u in a)if(a.hasOwnProperty(u)&&(D=a[u],D!=null))switch(u){case"value":h=D;break;case"defaultValue":S=D;break;case"multiple":o=D;default:Gt(t,n,u,D,a,null)}n=h,a=S,t.multiple=!!o,n!=null?Jn(t,!!o,n,!1):a!=null&&Jn(t,!!o,a,!0);return;case"textarea":vt("invalid",t),h=u=o=null;for(S in a)if(a.hasOwnProperty(S)&&(D=a[S],D!=null))switch(S){case"value":o=D;break;case"defaultValue":u=D;break;case"children":h=D;break;case"dangerouslySetInnerHTML":if(D!=null)throw Error(r(91));break;default:Gt(t,n,S,D,a,null)}ln(t,o,u,h);return;case"option":for(G in a)a.hasOwnProperty(G)&&(o=a[G],o!=null)&&(G==="selected"?t.selected=o&&typeof o!="function"&&typeof o!="symbol":Gt(t,n,G,o,a,null));return;case"dialog":vt("beforetoggle",t),vt("toggle",t),vt("cancel",t),vt("close",t);break;case"iframe":case"object":vt("load",t);break;case"video":case"audio":for(o=0;o<Fo.length;o++)vt(Fo[o],t);break;case"image":vt("error",t),vt("load",t);break;case"details":vt("toggle",t);break;case"embed":case"source":case"link":vt("error",t),vt("load",t);case"area":case"base":case"br":case"col":case"hr":case"keygen":case"meta":case"param":case"track":case"wbr":case"menuitem":for(ae in a)if(a.hasOwnProperty(ae)&&(o=a[ae],o!=null))switch(ae){case"children":case"dangerouslySetInnerHTML":throw Error(r(137,n));default:Gt(t,n,ae,o,a,null)}return;default:if(Ks(n)){for(_e in a)a.hasOwnProperty(_e)&&(o=a[_e],o!==void 0&&uh(t,n,_e,o,a,void 0));return}}for(D in a)a.hasOwnProperty(D)&&(o=a[D],o!=null&&Gt(t,n,D,o,a,null))}function cS(t,n,a,o){switch(n){case"div":case"span":case"svg":case"path":case"a":case"g":case"p":case"li":break;case"input":var u=null,h=null,S=null,D=null,G=null,ae=null,_e=null;for(ue in a){var Me=a[ue];if(a.hasOwnProperty(ue)&&Me!=null)switch(ue){case"checked":break;case"value":break;case"defaultValue":G=Me;default:o.hasOwnProperty(ue)||Gt(t,n,ue,null,o,Me)}}for(var le in o){var ue=o[le];if(Me=a[le],o.hasOwnProperty(le)&&(ue!=null||Me!=null))switch(le){case"type":h=ue;break;case"name":u=ue;break;case"checked":ae=ue;break;case"defaultChecked":_e=ue;break;case"value":S=ue;break;case"defaultValue":D=ue;break;case"children":case"dangerouslySetInnerHTML":if(ue!=null)throw Error(r(137,n));break;default:ue!==Me&&Gt(t,n,le,ue,o,Me)}}Pn(t,S,D,G,ae,_e,h,u);return;case"select":ue=S=D=le=null;for(h in a)if(G=a[h],a.hasOwnProperty(h)&&G!=null)switch(h){case"value":break;case"multiple":ue=G;default:o.hasOwnProperty(h)||Gt(t,n,h,null,o,G)}for(u in o)if(h=o[u],G=a[u],o.hasOwnProperty(u)&&(h!=null||G!=null))switch(u){case"value":le=h;break;case"defaultValue":D=h;break;case"multiple":S=h;default:h!==G&&Gt(t,n,u,h,o,G)}n=D,a=S,o=ue,le!=null?Jn(t,!!a,le,!1):!!o!=!!a&&(n!=null?Jn(t,!!a,n,!0):Jn(t,!!a,a?[]:"",!1));return;case"textarea":ue=le=null;for(D in a)if(u=a[D],a.hasOwnProperty(D)&&u!=null&&!o.hasOwnProperty(D))switch(D){case"value":break;case"children":break;default:Gt(t,n,D,null,o,u)}for(S in o)if(u=o[S],h=a[S],o.hasOwnProperty(S)&&(u!=null||h!=null))switch(S){case"value":le=u;break;case"defaultValue":ue=u;break;case"children":break;case"dangerouslySetInnerHTML":if(u!=null)throw Error(r(91));break;default:u!==h&&Gt(t,n,S,u,o,h)}Pt(t,le,ue);return;case"option":for(var ke in a)le=a[ke],a.hasOwnProperty(ke)&&le!=null&&!o.hasOwnProperty(ke)&&(ke==="selected"?t.selected=!1:Gt(t,n,ke,null,o,le));for(G in o)le=o[G],ue=a[G],o.hasOwnProperty(G)&&le!==ue&&(le!=null||ue!=null)&&(G==="selected"?t.selected=le&&typeof le!="function"&&typeof le!="symbol":Gt(t,n,G,le,o,ue));return;case"img":case"link":case"area":case"base":case"br":case"col":case"embed":case"hr":case"keygen":case"meta":case"param":case"source":case"track":case"wbr":case"menuitem":for(var et in a)le=a[et],a.hasOwnProperty(et)&&le!=null&&!o.hasOwnProperty(et)&&Gt(t,n,et,null,o,le);for(ae in o)if(le=o[ae],ue=a[ae],o.hasOwnProperty(ae)&&le!==ue&&(le!=null||ue!=null))switch(ae){case"children":case"dangerouslySetInnerHTML":if(le!=null)throw Error(r(137,n));break;default:Gt(t,n,ae,le,o,ue)}return;default:if(Ks(n)){for(var Vt in a)le=a[Vt],a.hasOwnProperty(Vt)&&le!==void 0&&!o.hasOwnProperty(Vt)&&uh(t,n,Vt,void 0,o,le);for(_e in o)le=o[_e],ue=a[_e],!o.hasOwnProperty(_e)||le===ue||le===void 0&&ue===void 0||uh(t,n,_e,le,o,ue);return}}for(var J in a)le=a[J],a.hasOwnProperty(J)&&le!=null&&!o.hasOwnProperty(J)&&Gt(t,n,J,null,o,le);for(Me in o)le=o[Me],ue=a[Me],!o.hasOwnProperty(Me)||le===ue||le==null&&ue==null||Gt(t,n,Me,le,o,ue)}function O_(t){switch(t){case"css":case"script":case"font":case"img":case"image":case"input":case"link":return!0;default:return!1}}function uS(){if(typeof performance.getEntriesByType=="function"){for(var t=0,n=0,a=performance.getEntriesByType("resource"),o=0;o<a.length;o++){var u=a[o],h=u.transferSize,S=u.initiatorType,D=u.duration;if(h&&D&&O_(S)){for(S=0,D=u.responseEnd,o+=1;o<a.length;o++){var G=a[o],ae=G.startTime;if(ae>D)break;var _e=G.transferSize,Me=G.initiatorType;_e&&O_(Me)&&(G=G.responseEnd,S+=_e*(G<D?1:(D-ae)/(G-ae)))}if(--o,n+=8*(h+S)/(u.duration/1e3),t++,10<t)break}}if(0<t)return n/t/1e6}return navigator.connection&&(t=navigator.connection.downlink,typeof t=="number")?t:5}var fh=null,hh=null;function mc(t){return t.nodeType===9?t:t.ownerDocument}function P_(t){switch(t){case"http://www.w3.org/2000/svg":return 1;case"http://www.w3.org/1998/Math/MathML":return 2;default:return 0}}function F_(t,n){if(t===0)switch(n){case"svg":return 1;case"math":return 2;default:return 0}return t===1&&n==="foreignObject"?0:t}function dh(t,n){return t==="textarea"||t==="noscript"||typeof n.children=="string"||typeof n.children=="number"||typeof n.children=="bigint"||typeof n.dangerouslySetInnerHTML=="object"&&n.dangerouslySetInnerHTML!==null&&n.dangerouslySetInnerHTML.__html!=null}var ph=null;function fS(){var t=window.event;return t&&t.type==="popstate"?t===ph?!1:(ph=t,!0):(ph=null,!1)}var I_=typeof setTimeout=="function"?setTimeout:void 0,hS=typeof clearTimeout=="function"?clearTimeout:void 0,z_=typeof Promise=="function"?Promise:void 0,dS=typeof queueMicrotask=="function"?queueMicrotask:typeof z_<"u"?function(t){return z_.resolve(null).then(t).catch(pS)}:I_;function pS(t){setTimeout(function(){throw t})}function Ja(t){return t==="head"}function B_(t,n){var a=n,o=0;do{var u=a.nextSibling;if(t.removeChild(a),u&&u.nodeType===8)if(a=u.data,a==="/$"||a==="/&"){if(o===0){t.removeChild(u),Rr(n);return}o--}else if(a==="$"||a==="$?"||a==="$~"||a==="$!"||a==="&")o++;else if(a==="html")zo(t.ownerDocument.documentElement);else if(a==="head"){a=t.ownerDocument.head,zo(a);for(var h=a.firstChild;h;){var S=h.nextSibling,D=h.nodeName;h[gs]||D==="SCRIPT"||D==="STYLE"||D==="LINK"&&h.rel.toLowerCase()==="stylesheet"||a.removeChild(h),h=S}}else a==="body"&&zo(t.ownerDocument.body);a=u}while(a);Rr(n)}function H_(t,n){var a=t;t=0;do{var o=a.nextSibling;if(a.nodeType===1?n?(a._stashedDisplay=a.style.display,a.style.display="none"):(a.style.display=a._stashedDisplay||"",a.getAttribute("style")===""&&a.removeAttribute("style")):a.nodeType===3&&(n?(a._stashedText=a.nodeValue,a.nodeValue=""):a.nodeValue=a._stashedText||""),o&&o.nodeType===8)if(a=o.data,a==="/$"){if(t===0)break;t--}else a!=="$"&&a!=="$?"&&a!=="$~"&&a!=="$!"||t++;a=o}while(a)}function mh(t){var n=t.firstChild;for(n&&n.nodeType===10&&(n=n.nextSibling);n;){var a=n;switch(n=n.nextSibling,a.nodeName){case"HTML":case"HEAD":case"BODY":mh(a),no(a);continue;case"SCRIPT":case"STYLE":continue;case"LINK":if(a.rel.toLowerCase()==="stylesheet")continue}t.removeChild(a)}}function mS(t,n,a,o){for(;t.nodeType===1;){var u=a;if(t.nodeName.toLowerCase()!==n.toLowerCase()){if(!o&&(t.nodeName!=="INPUT"||t.type!=="hidden"))break}else if(o){if(!t[gs])switch(n){case"meta":if(!t.hasAttribute("itemprop"))break;return t;case"link":if(h=t.getAttribute("rel"),h==="stylesheet"&&t.hasAttribute("data-precedence"))break;if(h!==u.rel||t.getAttribute("href")!==(u.href==null||u.href===""?null:u.href)||t.getAttribute("crossorigin")!==(u.crossOrigin==null?null:u.crossOrigin)||t.getAttribute("title")!==(u.title==null?null:u.title))break;return t;case"style":if(t.hasAttribute("data-precedence"))break;return t;case"script":if(h=t.getAttribute("src"),(h!==(u.src==null?null:u.src)||t.getAttribute("type")!==(u.type==null?null:u.type)||t.getAttribute("crossorigin")!==(u.crossOrigin==null?null:u.crossOrigin))&&h&&t.hasAttribute("async")&&!t.hasAttribute("itemprop"))break;return t;default:return t}}else if(n==="input"&&t.type==="hidden"){var h=u.name==null?null:""+u.name;if(u.type==="hidden"&&t.getAttribute("name")===h)return t}else return t;if(t=mi(t.nextSibling),t===null)break}return null}function gS(t,n,a){if(n==="")return null;for(;t.nodeType!==3;)if((t.nodeType!==1||t.nodeName!=="INPUT"||t.type!=="hidden")&&!a||(t=mi(t.nextSibling),t===null))return null;return t}function G_(t,n){for(;t.nodeType!==8;)if((t.nodeType!==1||t.nodeName!=="INPUT"||t.type!=="hidden")&&!n||(t=mi(t.nextSibling),t===null))return null;return t}function gh(t){return t.data==="$?"||t.data==="$~"}function _h(t){return t.data==="$!"||t.data==="$?"&&t.ownerDocument.readyState!=="loading"}function _S(t,n){var a=t.ownerDocument;if(t.data==="$~")t._reactRetry=n;else if(t.data!=="$?"||a.readyState!=="loading")n();else{var o=function(){n(),a.removeEventListener("DOMContentLoaded",o)};a.addEventListener("DOMContentLoaded",o),t._reactRetry=o}}function mi(t){for(;t!=null;t=t.nextSibling){var n=t.nodeType;if(n===1||n===3)break;if(n===8){if(n=t.data,n==="$"||n==="$!"||n==="$?"||n==="$~"||n==="&"||n==="F!"||n==="F")break;if(n==="/$"||n==="/&")return null}}return t}var vh=null;function V_(t){t=t.nextSibling;for(var n=0;t;){if(t.nodeType===8){var a=t.data;if(a==="/$"||a==="/&"){if(n===0)return mi(t.nextSibling);n--}else a!=="$"&&a!=="$!"&&a!=="$?"&&a!=="$~"&&a!=="&"||n++}t=t.nextSibling}return null}function k_(t){t=t.previousSibling;for(var n=0;t;){if(t.nodeType===8){var a=t.data;if(a==="$"||a==="$!"||a==="$?"||a==="$~"||a==="&"){if(n===0)return t;n--}else a!=="/$"&&a!=="/&"||n++}t=t.previousSibling}return null}function j_(t,n,a){switch(n=mc(a),t){case"html":if(t=n.documentElement,!t)throw Error(r(452));return t;case"head":if(t=n.head,!t)throw Error(r(453));return t;case"body":if(t=n.body,!t)throw Error(r(454));return t;default:throw Error(r(451))}}function zo(t){for(var n=t.attributes;n.length;)t.removeAttributeNode(n[0]);no(t)}var gi=new Map,X_=new Set;function gc(t){return typeof t.getRootNode=="function"?t.getRootNode():t.nodeType===9?t:t.ownerDocument}var ma=B.d;B.d={f:vS,r:xS,D:yS,C:SS,L:MS,m:ES,X:TS,S:bS,M:AS};function vS(){var t=ma.f(),n=oc();return t||n}function xS(t){var n=Oa(t);n!==null&&n.tag===5&&n.type==="form"?lg(n):ma.r(t)}var br=typeof document>"u"?null:document;function W_(t,n,a){var o=br;if(o&&typeof n=="string"&&n){var u=at(n);u='link[rel="'+t+'"][href="'+u+'"]',typeof a=="string"&&(u+='[crossorigin="'+a+'"]'),X_.has(u)||(X_.add(u),t={rel:t,crossOrigin:a,href:n},o.querySelector(u)===null&&(n=o.createElement("link"),An(n,"link",t),W(n),o.head.appendChild(n)))}}function yS(t){ma.D(t),W_("dns-prefetch",t,null)}function SS(t,n){ma.C(t,n),W_("preconnect",t,n)}function MS(t,n,a){ma.L(t,n,a);var o=br;if(o&&t&&n){var u='link[rel="preload"][as="'+at(n)+'"]';n==="image"&&a&&a.imageSrcSet?(u+='[imagesrcset="'+at(a.imageSrcSet)+'"]',typeof a.imageSizes=="string"&&(u+='[imagesizes="'+at(a.imageSizes)+'"]')):u+='[href="'+at(t)+'"]';var h=u;switch(n){case"style":h=Tr(t);break;case"script":h=Ar(t)}gi.has(h)||(t=v({rel:"preload",href:n==="image"&&a&&a.imageSrcSet?void 0:t,as:n},a),gi.set(h,t),o.querySelector(u)!==null||n==="style"&&o.querySelector(Bo(h))||n==="script"&&o.querySelector(Ho(h))||(n=o.createElement("link"),An(n,"link",t),W(n),o.head.appendChild(n)))}}function ES(t,n){ma.m(t,n);var a=br;if(a&&t){var o=n&&typeof n.as=="string"?n.as:"script",u='link[rel="modulepreload"][as="'+at(o)+'"][href="'+at(t)+'"]',h=u;switch(o){case"audioworklet":case"paintworklet":case"serviceworker":case"sharedworker":case"worker":case"script":h=Ar(t)}if(!gi.has(h)&&(t=v({rel:"modulepreload",href:t},n),gi.set(h,t),a.querySelector(u)===null)){switch(o){case"audioworklet":case"paintworklet":case"serviceworker":case"sharedworker":case"worker":case"script":if(a.querySelector(Ho(h)))return}o=a.createElement("link"),An(o,"link",t),W(o),a.head.appendChild(o)}}}function bS(t,n,a){ma.S(t,n,a);var o=br;if(o&&t){var u=N(o).hoistableStyles,h=Tr(t);n=n||"default";var S=u.get(h);if(!S){var D={loading:0,preload:null};if(S=o.querySelector(Bo(h)))D.loading=5;else{t=v({rel:"stylesheet",href:t,"data-precedence":n},a),(a=gi.get(h))&&xh(t,a);var G=S=o.createElement("link");W(G),An(G,"link",t),G._p=new Promise(function(ae,_e){G.onload=ae,G.onerror=_e}),G.addEventListener("load",function(){D.loading|=1}),G.addEventListener("error",function(){D.loading|=2}),D.loading|=4,_c(S,n,o)}S={type:"stylesheet",instance:S,count:1,state:D},u.set(h,S)}}}function TS(t,n){ma.X(t,n);var a=br;if(a&&t){var o=N(a).hoistableScripts,u=Ar(t),h=o.get(u);h||(h=a.querySelector(Ho(u)),h||(t=v({src:t,async:!0},n),(n=gi.get(u))&&yh(t,n),h=a.createElement("script"),W(h),An(h,"link",t),a.head.appendChild(h)),h={type:"script",instance:h,count:1,state:null},o.set(u,h))}}function AS(t,n){ma.M(t,n);var a=br;if(a&&t){var o=N(a).hoistableScripts,u=Ar(t),h=o.get(u);h||(h=a.querySelector(Ho(u)),h||(t=v({src:t,async:!0,type:"module"},n),(n=gi.get(u))&&yh(t,n),h=a.createElement("script"),W(h),An(h,"link",t),a.head.appendChild(h)),h={type:"script",instance:h,count:1,state:null},o.set(u,h))}}function q_(t,n,a,o){var u=(u=ie.current)?gc(u):null;if(!u)throw Error(r(446));switch(t){case"meta":case"title":return null;case"style":return typeof a.precedence=="string"&&typeof a.href=="string"?(n=Tr(a.href),a=N(u).hoistableStyles,o=a.get(n),o||(o={type:"style",instance:null,count:0,state:null},a.set(n,o)),o):{type:"void",instance:null,count:0,state:null};case"link":if(a.rel==="stylesheet"&&typeof a.href=="string"&&typeof a.precedence=="string"){t=Tr(a.href);var h=N(u).hoistableStyles,S=h.get(t);if(S||(u=u.ownerDocument||u,S={type:"stylesheet",instance:null,count:0,state:{loading:0,preload:null}},h.set(t,S),(h=u.querySelector(Bo(t)))&&!h._p&&(S.instance=h,S.state.loading=5),gi.has(t)||(a={rel:"preload",as:"style",href:a.href,crossOrigin:a.crossOrigin,integrity:a.integrity,media:a.media,hrefLang:a.hrefLang,referrerPolicy:a.referrerPolicy},gi.set(t,a),h||RS(u,t,a,S.state))),n&&o===null)throw Error(r(528,""));return S}if(n&&o!==null)throw Error(r(529,""));return null;case"script":return n=a.async,a=a.src,typeof a=="string"&&n&&typeof n!="function"&&typeof n!="symbol"?(n=Ar(a),a=N(u).hoistableScripts,o=a.get(n),o||(o={type:"script",instance:null,count:0,state:null},a.set(n,o)),o):{type:"void",instance:null,count:0,state:null};default:throw Error(r(444,t))}}function Tr(t){return'href="'+at(t)+'"'}function Bo(t){return'link[rel="stylesheet"]['+t+"]"}function Y_(t){return v({},t,{"data-precedence":t.precedence,precedence:null})}function RS(t,n,a,o){t.querySelector('link[rel="preload"][as="style"]['+n+"]")?o.loading=1:(n=t.createElement("link"),o.preload=n,n.addEventListener("load",function(){return o.loading|=1}),n.addEventListener("error",function(){return o.loading|=2}),An(n,"link",a),W(n),t.head.appendChild(n))}function Ar(t){return'[src="'+at(t)+'"]'}function Ho(t){return"script[async]"+t}function Z_(t,n,a){if(n.count++,n.instance===null)switch(n.type){case"style":var o=t.querySelector('style[data-href~="'+at(a.href)+'"]');if(o)return n.instance=o,W(o),o;var u=v({},a,{"data-href":a.href,"data-precedence":a.precedence,href:null,precedence:null});return o=(t.ownerDocument||t).createElement("style"),W(o),An(o,"style",u),_c(o,a.precedence,t),n.instance=o;case"stylesheet":u=Tr(a.href);var h=t.querySelector(Bo(u));if(h)return n.state.loading|=4,n.instance=h,W(h),h;o=Y_(a),(u=gi.get(u))&&xh(o,u),h=(t.ownerDocument||t).createElement("link"),W(h);var S=h;return S._p=new Promise(function(D,G){S.onload=D,S.onerror=G}),An(h,"link",o),n.state.loading|=4,_c(h,a.precedence,t),n.instance=h;case"script":return h=Ar(a.src),(u=t.querySelector(Ho(h)))?(n.instance=u,W(u),u):(o=a,(u=gi.get(h))&&(o=v({},a),yh(o,u)),t=t.ownerDocument||t,u=t.createElement("script"),W(u),An(u,"link",o),t.head.appendChild(u),n.instance=u);case"void":return null;default:throw Error(r(443,n.type))}else n.type==="stylesheet"&&(n.state.loading&4)===0&&(o=n.instance,n.state.loading|=4,_c(o,a.precedence,t));return n.instance}function _c(t,n,a){for(var o=a.querySelectorAll('link[rel="stylesheet"][data-precedence],style[data-precedence]'),u=o.length?o[o.length-1]:null,h=u,S=0;S<o.length;S++){var D=o[S];if(D.dataset.precedence===n)h=D;else if(h!==u)break}h?h.parentNode.insertBefore(t,h.nextSibling):(n=a.nodeType===9?a.head:a,n.insertBefore(t,n.firstChild))}function xh(t,n){t.crossOrigin==null&&(t.crossOrigin=n.crossOrigin),t.referrerPolicy==null&&(t.referrerPolicy=n.referrerPolicy),t.title==null&&(t.title=n.title)}function yh(t,n){t.crossOrigin==null&&(t.crossOrigin=n.crossOrigin),t.referrerPolicy==null&&(t.referrerPolicy=n.referrerPolicy),t.integrity==null&&(t.integrity=n.integrity)}var vc=null;function K_(t,n,a){if(vc===null){var o=new Map,u=vc=new Map;u.set(a,o)}else u=vc,o=u.get(a),o||(o=new Map,u.set(a,o));if(o.has(t))return o;for(o.set(t,null),a=a.getElementsByTagName(t),u=0;u<a.length;u++){var h=a[u];if(!(h[gs]||h[on]||t==="link"&&h.getAttribute("rel")==="stylesheet")&&h.namespaceURI!=="http://www.w3.org/2000/svg"){var S=h.getAttribute(n)||"";S=t+S;var D=o.get(S);D?D.push(h):o.set(S,[h])}}return o}function Q_(t,n,a){t=t.ownerDocument||t,t.head.insertBefore(a,n==="title"?t.querySelector("head > title"):null)}function CS(t,n,a){if(a===1||n.itemProp!=null)return!1;switch(t){case"meta":case"title":return!0;case"style":if(typeof n.precedence!="string"||typeof n.href!="string"||n.href==="")break;return!0;case"link":if(typeof n.rel!="string"||typeof n.href!="string"||n.href===""||n.onLoad||n.onError)break;return n.rel==="stylesheet"?(t=n.disabled,typeof n.precedence=="string"&&t==null):!0;case"script":if(n.async&&typeof n.async!="function"&&typeof n.async!="symbol"&&!n.onLoad&&!n.onError&&n.src&&typeof n.src=="string")return!0}return!1}function J_(t){return!(t.type==="stylesheet"&&(t.state.loading&3)===0)}function wS(t,n,a,o){if(a.type==="stylesheet"&&(typeof o.media!="string"||matchMedia(o.media).matches!==!1)&&(a.state.loading&4)===0){if(a.instance===null){var u=Tr(o.href),h=n.querySelector(Bo(u));if(h){n=h._p,n!==null&&typeof n=="object"&&typeof n.then=="function"&&(t.count++,t=xc.bind(t),n.then(t,t)),a.state.loading|=4,a.instance=h,W(h);return}h=n.ownerDocument||n,o=Y_(o),(u=gi.get(u))&&xh(o,u),h=h.createElement("link"),W(h);var S=h;S._p=new Promise(function(D,G){S.onload=D,S.onerror=G}),An(h,"link",o),a.instance=h}t.stylesheets===null&&(t.stylesheets=new Map),t.stylesheets.set(a,n),(n=a.state.preload)&&(a.state.loading&3)===0&&(t.count++,a=xc.bind(t),n.addEventListener("load",a),n.addEventListener("error",a))}}var Sh=0;function DS(t,n){return t.stylesheets&&t.count===0&&Sc(t,t.stylesheets),0<t.count||0<t.imgCount?function(a){var o=setTimeout(function(){if(t.stylesheets&&Sc(t,t.stylesheets),t.unsuspend){var h=t.unsuspend;t.unsuspend=null,h()}},6e4+n);0<t.imgBytes&&Sh===0&&(Sh=62500*uS());var u=setTimeout(function(){if(t.waitingForImages=!1,t.count===0&&(t.stylesheets&&Sc(t,t.stylesheets),t.unsuspend)){var h=t.unsuspend;t.unsuspend=null,h()}},(t.imgBytes>Sh?50:800)+n);return t.unsuspend=a,function(){t.unsuspend=null,clearTimeout(o),clearTimeout(u)}}:null}function xc(){if(this.count--,this.count===0&&(this.imgCount===0||!this.waitingForImages)){if(this.stylesheets)Sc(this,this.stylesheets);else if(this.unsuspend){var t=this.unsuspend;this.unsuspend=null,t()}}}var yc=null;function Sc(t,n){t.stylesheets=null,t.unsuspend!==null&&(t.count++,yc=new Map,n.forEach(NS,t),yc=null,xc.call(t))}function NS(t,n){if(!(n.state.loading&4)){var a=yc.get(t);if(a)var o=a.get(null);else{a=new Map,yc.set(t,a);for(var u=t.querySelectorAll("link[data-precedence],style[data-precedence]"),h=0;h<u.length;h++){var S=u[h];(S.nodeName==="LINK"||S.getAttribute("media")!=="not all")&&(a.set(S.dataset.precedence,S),o=S)}o&&a.set(null,o)}u=n.instance,S=u.getAttribute("data-precedence"),h=a.get(S)||o,h===o&&a.set(null,u),a.set(S,u),this.count++,o=xc.bind(this),u.addEventListener("load",o),u.addEventListener("error",o),h?h.parentNode.insertBefore(u,h.nextSibling):(t=t.nodeType===9?t.head:t,t.insertBefore(u,t.firstChild)),n.state.loading|=4}}var Go={$$typeof:U,Provider:null,Consumer:null,_currentValue:$,_currentValue2:$,_threadCount:0};function US(t,n,a,o,u,h,S,D,G){this.tag=1,this.containerInfo=t,this.pingCache=this.current=this.pendingChildren=null,this.timeoutHandle=-1,this.callbackNode=this.next=this.pendingContext=this.context=this.cancelPendingCommit=null,this.callbackPriority=0,this.expirationTimes=Tt(-1),this.entangledLanes=this.shellSuspendCounter=this.errorRecoveryDisabledLanes=this.expiredLanes=this.warmLanes=this.pingedLanes=this.suspendedLanes=this.pendingLanes=0,this.entanglements=Tt(0),this.hiddenUpdates=Tt(null),this.identifierPrefix=o,this.onUncaughtError=u,this.onCaughtError=h,this.onRecoverableError=S,this.pooledCache=null,this.pooledCacheLanes=0,this.formState=G,this.incompleteTransitions=new Map}function $_(t,n,a,o,u,h,S,D,G,ae,_e,Me){return t=new US(t,n,a,S,G,ae,_e,Me,D),n=1,h===!0&&(n|=24),h=ei(3,null,null,n),t.current=h,h.stateNode=t,n=$u(),n.refCount++,t.pooledCache=n,n.refCount++,h.memoizedState={element:o,isDehydrated:a,cache:n},af(h),t}function e0(t){return t?(t=ir,t):ir}function t0(t,n,a,o,u,h){u=e0(u),o.context===null?o.context=u:o.pendingContext=u,o=Ga(n),o.payload={element:a},h=h===void 0?null:h,h!==null&&(o.callback=h),a=Va(t,o,n),a!==null&&(Xn(a,t,n),xo(a,t,n))}function n0(t,n){if(t=t.memoizedState,t!==null&&t.dehydrated!==null){var a=t.retryLane;t.retryLane=a!==0&&a<n?a:n}}function Mh(t,n){n0(t,n),(t=t.alternate)&&n0(t,n)}function i0(t){if(t.tag===13||t.tag===31){var n=Ss(t,67108864);n!==null&&Xn(n,t,67108864),Mh(t,67108864)}}function a0(t){if(t.tag===13||t.tag===31){var n=si();n=qs(n);var a=Ss(t,n);a!==null&&Xn(a,t,n),Mh(t,n)}}var Mc=!0;function LS(t,n,a,o){var u=I.T;I.T=null;var h=B.p;try{B.p=2,Eh(t,n,a,o)}finally{B.p=h,I.T=u}}function OS(t,n,a,o){var u=I.T;I.T=null;var h=B.p;try{B.p=8,Eh(t,n,a,o)}finally{B.p=h,I.T=u}}function Eh(t,n,a,o){if(Mc){var u=bh(o);if(u===null)ch(t,n,o,Ec,a),r0(t,o);else if(FS(u,t,n,a,o))o.stopPropagation();else if(r0(t,o),n&4&&-1<PS.indexOf(t)){for(;u!==null;){var h=Oa(u);if(h!==null)switch(h.tag){case 3:if(h=h.stateNode,h.current.memoizedState.isDehydrated){var S=Te(h.pendingLanes);if(S!==0){var D=h;for(D.pendingLanes|=2,D.entangledLanes|=2;S;){var G=1<<31-Pe(S);D.entanglements[1]|=G,S&=~G}Gi(h),(Ut&6)===0&&(sc=b()+500,Po(0))}}break;case 31:case 13:D=Ss(h,2),D!==null&&Xn(D,h,2),oc(),Mh(h,2)}if(h=bh(o),h===null&&ch(t,n,o,Ec,a),h===u)break;u=h}u!==null&&o.stopPropagation()}else ch(t,n,o,null,a)}}function bh(t){return t=Tu(t),Th(t)}var Ec=null;function Th(t){if(Ec=null,t=La(t),t!==null){var n=c(t);if(n===null)t=null;else{var a=n.tag;if(a===13){if(t=f(n),t!==null)return t;t=null}else if(a===31){if(t=p(n),t!==null)return t;t=null}else if(a===3){if(n.stateNode.current.memoizedState.isDehydrated)return n.tag===3?n.stateNode.containerInfo:null;t=null}else n!==t&&(t=null)}}return Ec=t,null}function s0(t){switch(t){case"beforetoggle":case"cancel":case"click":case"close":case"contextmenu":case"copy":case"cut":case"auxclick":case"dblclick":case"dragend":case"dragstart":case"drop":case"focusin":case"focusout":case"input":case"invalid":case"keydown":case"keypress":case"keyup":case"mousedown":case"mouseup":case"paste":case"pause":case"play":case"pointercancel":case"pointerdown":case"pointerup":case"ratechange":case"reset":case"resize":case"seeked":case"submit":case"toggle":case"touchcancel":case"touchend":case"touchstart":case"volumechange":case"change":case"selectionchange":case"textInput":case"compositionstart":case"compositionend":case"compositionupdate":case"beforeblur":case"afterblur":case"beforeinput":case"blur":case"fullscreenchange":case"focus":case"hashchange":case"popstate":case"select":case"selectstart":return 2;case"drag":case"dragenter":case"dragexit":case"dragleave":case"dragover":case"mousemove":case"mouseout":case"mouseover":case"pointermove":case"pointerout":case"pointerover":case"scroll":case"touchmove":case"wheel":case"mouseenter":case"mouseleave":case"pointerenter":case"pointerleave":return 8;case"message":switch(Z()){case xe:return 2;case Ee:return 8;case ge:case Xe:return 32;case De:return 268435456;default:return 32}default:return 32}}var Ah=!1,$a=null,es=null,ts=null,Vo=new Map,ko=new Map,ns=[],PS="mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset".split(" ");function r0(t,n){switch(t){case"focusin":case"focusout":$a=null;break;case"dragenter":case"dragleave":es=null;break;case"mouseover":case"mouseout":ts=null;break;case"pointerover":case"pointerout":Vo.delete(n.pointerId);break;case"gotpointercapture":case"lostpointercapture":ko.delete(n.pointerId)}}function jo(t,n,a,o,u,h){return t===null||t.nativeEvent!==h?(t={blockedOn:n,domEventName:a,eventSystemFlags:o,nativeEvent:h,targetContainers:[u]},n!==null&&(n=Oa(n),n!==null&&i0(n)),t):(t.eventSystemFlags|=o,n=t.targetContainers,u!==null&&n.indexOf(u)===-1&&n.push(u),t)}function FS(t,n,a,o,u){switch(n){case"focusin":return $a=jo($a,t,n,a,o,u),!0;case"dragenter":return es=jo(es,t,n,a,o,u),!0;case"mouseover":return ts=jo(ts,t,n,a,o,u),!0;case"pointerover":var h=u.pointerId;return Vo.set(h,jo(Vo.get(h)||null,t,n,a,o,u)),!0;case"gotpointercapture":return h=u.pointerId,ko.set(h,jo(ko.get(h)||null,t,n,a,o,u)),!0}return!1}function o0(t){var n=La(t.target);if(n!==null){var a=c(n);if(a!==null){if(n=a.tag,n===13){if(n=f(a),n!==null){t.blockedOn=n,Zs(t.priority,function(){a0(a)});return}}else if(n===31){if(n=p(a),n!==null){t.blockedOn=n,Zs(t.priority,function(){a0(a)});return}}else if(n===3&&a.stateNode.current.memoizedState.isDehydrated){t.blockedOn=a.tag===3?a.stateNode.containerInfo:null;return}}}t.blockedOn=null}function bc(t){if(t.blockedOn!==null)return!1;for(var n=t.targetContainers;0<n.length;){var a=bh(t.nativeEvent);if(a===null){a=t.nativeEvent;var o=new a.constructor(a.type,a);bu=o,a.target.dispatchEvent(o),bu=null}else return n=Oa(a),n!==null&&i0(n),t.blockedOn=a,!1;n.shift()}return!0}function l0(t,n,a){bc(t)&&a.delete(n)}function IS(){Ah=!1,$a!==null&&bc($a)&&($a=null),es!==null&&bc(es)&&(es=null),ts!==null&&bc(ts)&&(ts=null),Vo.forEach(l0),ko.forEach(l0)}function Tc(t,n){t.blockedOn===n&&(t.blockedOn=null,Ah||(Ah=!0,s.unstable_scheduleCallback(s.unstable_NormalPriority,IS)))}var Ac=null;function c0(t){Ac!==t&&(Ac=t,s.unstable_scheduleCallback(s.unstable_NormalPriority,function(){Ac===t&&(Ac=null);for(var n=0;n<t.length;n+=3){var a=t[n],o=t[n+1],u=t[n+2];if(typeof o!="function"){if(Th(o||a)===null)continue;break}var h=Oa(a);h!==null&&(t.splice(n,3),n-=3,bf(h,{pending:!0,data:u,method:a.method,action:o},o,u))}}))}function Rr(t){function n(G){return Tc(G,t)}$a!==null&&Tc($a,t),es!==null&&Tc(es,t),ts!==null&&Tc(ts,t),Vo.forEach(n),ko.forEach(n);for(var a=0;a<ns.length;a++){var o=ns[a];o.blockedOn===t&&(o.blockedOn=null)}for(;0<ns.length&&(a=ns[0],a.blockedOn===null);)o0(a),a.blockedOn===null&&ns.shift();if(a=(t.ownerDocument||t).$$reactFormReplay,a!=null)for(o=0;o<a.length;o+=3){var u=a[o],h=a[o+1],S=u[mn]||null;if(typeof h=="function")S||c0(a);else if(S){var D=null;if(h&&h.hasAttribute("formAction")){if(u=h,S=h[mn]||null)D=S.formAction;else if(Th(u)!==null)continue}else D=S.action;typeof D=="function"?a[o+1]=D:(a.splice(o,3),o-=3),c0(a)}}}function u0(){function t(h){h.canIntercept&&h.info==="react-transition"&&h.intercept({handler:function(){return new Promise(function(S){return u=S})},focusReset:"manual",scroll:"manual"})}function n(){u!==null&&(u(),u=null),o||setTimeout(a,20)}function a(){if(!o&&!navigation.transition){var h=navigation.currentEntry;h&&h.url!=null&&navigation.navigate(h.url,{state:h.getState(),info:"react-transition",history:"replace"})}}if(typeof navigation=="object"){var o=!1,u=null;return navigation.addEventListener("navigate",t),navigation.addEventListener("navigatesuccess",n),navigation.addEventListener("navigateerror",n),setTimeout(a,100),function(){o=!0,navigation.removeEventListener("navigate",t),navigation.removeEventListener("navigatesuccess",n),navigation.removeEventListener("navigateerror",n),u!==null&&(u(),u=null)}}}function Rh(t){this._internalRoot=t}Rc.prototype.render=Rh.prototype.render=function(t){var n=this._internalRoot;if(n===null)throw Error(r(409));var a=n.current,o=si();t0(a,o,t,n,null,null)},Rc.prototype.unmount=Rh.prototype.unmount=function(){var t=this._internalRoot;if(t!==null){this._internalRoot=null;var n=t.containerInfo;t0(t.current,2,null,t,null,null),oc(),n[Qi]=null}};function Rc(t){this._internalRoot=t}Rc.prototype.unstable_scheduleHydration=function(t){if(t){var n=Ii();t={blockedOn:null,target:t,priority:n};for(var a=0;a<ns.length&&n!==0&&n<ns[a].priority;a++);ns.splice(a,0,t),a===0&&o0(t)}};var f0=e.version;if(f0!=="19.2.4")throw Error(r(527,f0,"19.2.4"));B.findDOMNode=function(t){var n=t._reactInternals;if(n===void 0)throw typeof t.render=="function"?Error(r(188)):(t=Object.keys(t).join(","),Error(r(268,t)));return t=d(n),t=t!==null?_(t):null,t=t===null?null:t.stateNode,t};var zS={bundleType:0,version:"19.2.4",rendererPackageName:"react-dom",currentDispatcherRef:I,reconcilerVersion:"19.2.4"};if(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__<"u"){var Cc=__REACT_DEVTOOLS_GLOBAL_HOOK__;if(!Cc.isDisabled&&Cc.supportsFiber)try{Re=Cc.inject(zS),be=Cc}catch{}}return Wo.createRoot=function(t,n){if(!l(t))throw Error(r(299));var a=!1,o="",u=vg,h=xg,S=yg;return n!=null&&(n.unstable_strictMode===!0&&(a=!0),n.identifierPrefix!==void 0&&(o=n.identifierPrefix),n.onUncaughtError!==void 0&&(u=n.onUncaughtError),n.onCaughtError!==void 0&&(h=n.onCaughtError),n.onRecoverableError!==void 0&&(S=n.onRecoverableError)),n=$_(t,1,!1,null,null,a,o,null,u,h,S,u0),t[Qi]=n.current,lh(t),new Rh(n)},Wo.hydrateRoot=function(t,n,a){if(!l(t))throw Error(r(299));var o=!1,u="",h=vg,S=xg,D=yg,G=null;return a!=null&&(a.unstable_strictMode===!0&&(o=!0),a.identifierPrefix!==void 0&&(u=a.identifierPrefix),a.onUncaughtError!==void 0&&(h=a.onUncaughtError),a.onCaughtError!==void 0&&(S=a.onCaughtError),a.onRecoverableError!==void 0&&(D=a.onRecoverableError),a.formState!==void 0&&(G=a.formState)),n=$_(t,1,!0,n,a??null,o,u,G,h,S,D,u0),n.context=e0(null),a=n.current,o=si(),o=qs(o),u=Ga(o),u.callback=null,Va(a,u,o),a=o,n.current.lanes=a,Ln(n,a),Gi(n),t[Qi]=n.current,lh(t),new Rc(n)},Wo.version="19.2.4",Wo}var S0;function YS(){if(S0)return Dh.exports;S0=1;function s(){if(!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__>"u"||typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE!="function"))try{__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(s)}catch(e){console.error(e)}}return s(),Dh.exports=qS(),Dh.exports}var ZS=YS();var M0="popstate";function KS(s={}){function e(r,l){let{pathname:c,search:f,hash:p}=r.location;return gd("",{pathname:c,search:f,hash:p},l.state&&l.state.usr||null,l.state&&l.state.key||"default")}function i(r,l){return typeof l=="string"?l:sl(l)}return JS(e,i,null,s)}function Qt(s,e){if(s===!1||s===null||typeof s>"u")throw new Error(e)}function Oi(s,e){if(!s){typeof console<"u"&&console.warn(e);try{throw new Error(e)}catch{}}}function QS(){return Math.random().toString(36).substring(2,10)}function E0(s,e){return{usr:s.state,key:s.key,idx:e}}function gd(s,e,i=null,r){return{pathname:typeof s=="string"?s:s.pathname,search:"",hash:"",...typeof e=="string"?Qr(e):e,state:i,key:e&&e.key||r||QS()}}function sl({pathname:s="/",search:e="",hash:i=""}){return e&&e!=="?"&&(s+=e.charAt(0)==="?"?e:"?"+e),i&&i!=="#"&&(s+=i.charAt(0)==="#"?i:"#"+i),s}function Qr(s){let e={};if(s){let i=s.indexOf("#");i>=0&&(e.hash=s.substring(i),s=s.substring(0,i));let r=s.indexOf("?");r>=0&&(e.search=s.substring(r),s=s.substring(0,r)),s&&(e.pathname=s)}return e}function JS(s,e,i,r={}){let{window:l=document.defaultView,v5Compat:c=!1}=r,f=l.history,p="POP",m=null,d=_();d==null&&(d=0,f.replaceState({...f.state,idx:d},""));function _(){return(f.state||{idx:null}).idx}function v(){p="POP";let x=_(),y=x==null?null:x-d;d=x,m&&m({action:p,location:R.location,delta:y})}function g(x,y){p="PUSH";let T=gd(R.location,x,y);d=_()+1;let U=E0(T,d),P=R.createHref(T);try{f.pushState(U,"",P)}catch(V){if(V instanceof DOMException&&V.name==="DataCloneError")throw V;l.location.assign(P)}c&&m&&m({action:p,location:R.location,delta:1})}function M(x,y){p="REPLACE";let T=gd(R.location,x,y);d=_();let U=E0(T,d),P=R.createHref(T);f.replaceState(U,"",P),c&&m&&m({action:p,location:R.location,delta:0})}function E(x){return $S(x)}let R={get action(){return p},get location(){return s(l,f)},listen(x){if(m)throw new Error("A history only accepts one active listener");return l.addEventListener(M0,v),m=x,()=>{l.removeEventListener(M0,v),m=null}},createHref(x){return e(l,x)},createURL:E,encodeLocation(x){let y=E(x);return{pathname:y.pathname,search:y.search,hash:y.hash}},push:g,replace:M,go(x){return f.go(x)}};return R}function $S(s,e=!1){let i="http://localhost";typeof window<"u"&&(i=window.location.origin!=="null"?window.location.origin:window.location.href),Qt(i,"No window.location.(origin|href) available to create URL");let r=typeof s=="string"?s:sl(s);return r=r.replace(/ $/,"%20"),!e&&r.startsWith("//")&&(r=i+r),new URL(r,i)}function Lv(s,e,i="/"){return eM(s,e,i,!1)}function eM(s,e,i,r){let l=typeof e=="string"?Qr(e):e,c=Ra(l.pathname||"/",i);if(c==null)return null;let f=Ov(s);tM(f);let p=null;for(let m=0;p==null&&m<f.length;++m){let d=hM(c);p=uM(f[m],d,r)}return p}function Ov(s,e=[],i=[],r="",l=!1){let c=(f,p,m=l,d)=>{let _={relativePath:d===void 0?f.path||"":d,caseSensitive:f.caseSensitive===!0,childrenIndex:p,route:f};if(_.relativePath.startsWith("/")){if(!_.relativePath.startsWith(r)&&m)return;Qt(_.relativePath.startsWith(r),`Absolute route path "${_.relativePath}" nested under path "${r}" is not valid. An absolute child route path must start with the combined path of all its parent routes.`),_.relativePath=_.relativePath.slice(r.length)}let v=Ea([r,_.relativePath]),g=i.concat(_);f.children&&f.children.length>0&&(Qt(f.index!==!0,`Index routes must not have child routes. Please remove all child routes from route path "${v}".`),Ov(f.children,e,g,v,m)),!(f.path==null&&!f.index)&&e.push({path:v,score:lM(v,f.index),routesMeta:g})};return s.forEach((f,p)=>{if(f.path===""||!f.path?.includes("?"))c(f,p);else for(let m of Pv(f.path))c(f,p,!0,m)}),e}function Pv(s){let e=s.split("/");if(e.length===0)return[];let[i,...r]=e,l=i.endsWith("?"),c=i.replace(/\?$/,"");if(r.length===0)return l?[c,""]:[c];let f=Pv(r.join("/")),p=[];return p.push(...f.map(m=>m===""?c:[c,m].join("/"))),l&&p.push(...f),p.map(m=>s.startsWith("/")&&m===""?"/":m)}function tM(s){s.sort((e,i)=>e.score!==i.score?i.score-e.score:cM(e.routesMeta.map(r=>r.childrenIndex),i.routesMeta.map(r=>r.childrenIndex)))}var nM=/^:[\w-]+$/,iM=3,aM=2,sM=1,rM=10,oM=-2,b0=s=>s==="*";function lM(s,e){let i=s.split("/"),r=i.length;return i.some(b0)&&(r+=oM),e&&(r+=aM),i.filter(l=>!b0(l)).reduce((l,c)=>l+(nM.test(c)?iM:c===""?sM:rM),r)}function cM(s,e){return s.length===e.length&&s.slice(0,-1).every((r,l)=>r===e[l])?s[s.length-1]-e[e.length-1]:0}function uM(s,e,i=!1){let{routesMeta:r}=s,l={},c="/",f=[];for(let p=0;p<r.length;++p){let m=r[p],d=p===r.length-1,_=c==="/"?e:e.slice(c.length)||"/",v=fu({path:m.relativePath,caseSensitive:m.caseSensitive,end:d},_),g=m.route;if(!v&&d&&i&&!r[r.length-1].route.index&&(v=fu({path:m.relativePath,caseSensitive:m.caseSensitive,end:!1},_)),!v)return null;Object.assign(l,v.params),f.push({params:l,pathname:Ea([c,v.pathname]),pathnameBase:gM(Ea([c,v.pathnameBase])),route:g}),v.pathnameBase!=="/"&&(c=Ea([c,v.pathnameBase]))}return f}function fu(s,e){typeof s=="string"&&(s={path:s,caseSensitive:!1,end:!0});let[i,r]=fM(s.path,s.caseSensitive,s.end),l=e.match(i);if(!l)return null;let c=l[0],f=c.replace(/(.)\/+$/,"$1"),p=l.slice(1);return{params:r.reduce((d,{paramName:_,isOptional:v},g)=>{if(_==="*"){let E=p[g]||"";f=c.slice(0,c.length-E.length).replace(/(.)\/+$/,"$1")}const M=p[g];return v&&!M?d[_]=void 0:d[_]=(M||"").replace(/%2F/g,"/"),d},{}),pathname:c,pathnameBase:f,pattern:s}}function fM(s,e=!1,i=!0){Oi(s==="*"||!s.endsWith("*")||s.endsWith("/*"),`Route path "${s}" will be treated as if it were "${s.replace(/\*$/,"/*")}" because the \`*\` character must always follow a \`/\` in the pattern. To get rid of this warning, please change the route path to "${s.replace(/\*$/,"/*")}".`);let r=[],l="^"+s.replace(/\/*\*?$/,"").replace(/^\/*/,"/").replace(/[\\.*+^${}|()[\]]/g,"\\$&").replace(/\/:([\w-]+)(\?)?/g,(f,p,m)=>(r.push({paramName:p,isOptional:m!=null}),m?"/?([^\\/]+)?":"/([^\\/]+)")).replace(/\/([\w-]+)\?(\/|$)/g,"(/$1)?$2");return s.endsWith("*")?(r.push({paramName:"*"}),l+=s==="*"||s==="/*"?"(.*)$":"(?:\\/(.+)|\\/*)$"):i?l+="\\/*$":s!==""&&s!=="/"&&(l+="(?:(?=\\/|$))"),[new RegExp(l,e?void 0:"i"),r]}function hM(s){try{return s.split("/").map(e=>decodeURIComponent(e).replace(/\//g,"%2F")).join("/")}catch(e){return Oi(!1,`The URL path "${s}" could not be decoded because it is a malformed URL segment. This is probably due to a bad percent encoding (${e}).`),s}}function Ra(s,e){if(e==="/")return s;if(!s.toLowerCase().startsWith(e.toLowerCase()))return null;let i=e.endsWith("/")?e.length-1:e.length,r=s.charAt(i);return r&&r!=="/"?null:s.slice(i)||"/"}var dM=/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i;function pM(s,e="/"){let{pathname:i,search:r="",hash:l=""}=typeof s=="string"?Qr(s):s,c;return i?(i=i.replace(/\/\/+/g,"/"),i.startsWith("/")?c=T0(i.substring(1),"/"):c=T0(i,e)):c=e,{pathname:c,search:_M(r),hash:vM(l)}}function T0(s,e){let i=e.replace(/\/+$/,"").split("/");return s.split("/").forEach(l=>{l===".."?i.length>1&&i.pop():l!=="."&&i.push(l)}),i.length>1?i.join("/"):"/"}function Oh(s,e,i,r){return`Cannot include a '${s}' character in a manually specified \`to.${e}\` field [${JSON.stringify(r)}].  Please separate it out to the \`to.${i}\` field. Alternatively you may provide the full path as a string in <Link to="..."> and the router will parse it for you.`}function mM(s){return s.filter((e,i)=>i===0||e.route.path&&e.route.path.length>0)}function pp(s){let e=mM(s);return e.map((i,r)=>r===e.length-1?i.pathname:i.pathnameBase)}function mp(s,e,i,r=!1){let l;typeof s=="string"?l=Qr(s):(l={...s},Qt(!l.pathname||!l.pathname.includes("?"),Oh("?","pathname","search",l)),Qt(!l.pathname||!l.pathname.includes("#"),Oh("#","pathname","hash",l)),Qt(!l.search||!l.search.includes("#"),Oh("#","search","hash",l)));let c=s===""||l.pathname==="",f=c?"/":l.pathname,p;if(f==null)p=i;else{let v=e.length-1;if(!r&&f.startsWith("..")){let g=f.split("/");for(;g[0]==="..";)g.shift(),v-=1;l.pathname=g.join("/")}p=v>=0?e[v]:"/"}let m=pM(l,p),d=f&&f!=="/"&&f.endsWith("/"),_=(c||f===".")&&i.endsWith("/");return!m.pathname.endsWith("/")&&(d||_)&&(m.pathname+="/"),m}var Ea=s=>s.join("/").replace(/\/\/+/g,"/"),gM=s=>s.replace(/\/+$/,"").replace(/^\/*/,"/"),_M=s=>!s||s==="?"?"":s.startsWith("?")?s:"?"+s,vM=s=>!s||s==="#"?"":s.startsWith("#")?s:"#"+s,xM=class{constructor(s,e,i,r=!1){this.status=s,this.statusText=e||"",this.internal=r,i instanceof Error?(this.data=i.toString(),this.error=i):this.data=i}};function yM(s){return s!=null&&typeof s.status=="number"&&typeof s.statusText=="string"&&typeof s.internal=="boolean"&&"data"in s}function SM(s){return s.map(e=>e.route.path).filter(Boolean).join("/").replace(/\/\/*/g,"/")||"/"}var Fv=typeof window<"u"&&typeof window.document<"u"&&typeof window.document.createElement<"u";function Iv(s,e){let i=s;if(typeof i!="string"||!dM.test(i))return{absoluteURL:void 0,isExternal:!1,to:i};let r=i,l=!1;if(Fv)try{let c=new URL(window.location.href),f=i.startsWith("//")?new URL(c.protocol+i):new URL(i),p=Ra(f.pathname,e);f.origin===c.origin&&p!=null?i=p+f.search+f.hash:l=!0}catch{Oi(!1,`<Link to="${i}"> contains an invalid URL which will probably break when clicked - please update to a valid URL path.`)}return{absoluteURL:r,isExternal:l,to:i}}Object.getOwnPropertyNames(Object.prototype).sort().join("\0");var zv=["POST","PUT","PATCH","DELETE"];new Set(zv);var MM=["GET",...zv];new Set(MM);var Jr=K.createContext(null);Jr.displayName="DataRouter";var gu=K.createContext(null);gu.displayName="DataRouterState";var EM=K.createContext(!1),Bv=K.createContext({isTransitioning:!1});Bv.displayName="ViewTransition";var bM=K.createContext(new Map);bM.displayName="Fetchers";var TM=K.createContext(null);TM.displayName="Await";var li=K.createContext(null);li.displayName="Navigation";var ul=K.createContext(null);ul.displayName="Location";var Pi=K.createContext({outlet:null,matches:[],isDataRoute:!1});Pi.displayName="Route";var gp=K.createContext(null);gp.displayName="RouteError";var Hv="REACT_ROUTER_ERROR",AM="REDIRECT",RM="ROUTE_ERROR_RESPONSE";function CM(s){if(s.startsWith(`${Hv}:${AM}:{`))try{let e=JSON.parse(s.slice(28));if(typeof e=="object"&&e&&typeof e.status=="number"&&typeof e.statusText=="string"&&typeof e.location=="string"&&typeof e.reloadDocument=="boolean"&&typeof e.replace=="boolean")return e}catch{}}function wM(s){if(s.startsWith(`${Hv}:${RM}:{`))try{let e=JSON.parse(s.slice(40));if(typeof e=="object"&&e&&typeof e.status=="number"&&typeof e.statusText=="string")return new xM(e.status,e.statusText,e.data)}catch{}}function DM(s,{relative:e}={}){Qt($r(),"useHref() may be used only in the context of a <Router> component.");let{basename:i,navigator:r}=K.useContext(li),{hash:l,pathname:c,search:f}=fl(s,{relative:e}),p=c;return i!=="/"&&(p=c==="/"?i:Ea([i,c])),r.createHref({pathname:p,search:f,hash:l})}function $r(){return K.useContext(ul)!=null}function ms(){return Qt($r(),"useLocation() may be used only in the context of a <Router> component."),K.useContext(ul).location}var Gv="You should call navigate() in a React.useEffect(), not when your component is first rendered.";function Vv(s){K.useContext(li).static||K.useLayoutEffect(s)}function kv(){let{isDataRoute:s}=K.useContext(Pi);return s?jM():NM()}function NM(){Qt($r(),"useNavigate() may be used only in the context of a <Router> component.");let s=K.useContext(Jr),{basename:e,navigator:i}=K.useContext(li),{matches:r}=K.useContext(Pi),{pathname:l}=ms(),c=JSON.stringify(pp(r)),f=K.useRef(!1);return Vv(()=>{f.current=!0}),K.useCallback((m,d={})=>{if(Oi(f.current,Gv),!f.current)return;if(typeof m=="number"){i.go(m);return}let _=mp(m,JSON.parse(c),l,d.relative==="path");s==null&&e!=="/"&&(_.pathname=_.pathname==="/"?e:Ea([e,_.pathname])),(d.replace?i.replace:i.push)(_,d.state,d)},[e,i,c,l,s])}K.createContext(null);function UM(){let{matches:s}=K.useContext(Pi),e=s[s.length-1];return e?e.params:{}}function fl(s,{relative:e}={}){let{matches:i}=K.useContext(Pi),{pathname:r}=ms(),l=JSON.stringify(pp(i));return K.useMemo(()=>mp(s,JSON.parse(l),r,e==="path"),[s,l,r,e])}function LM(s,e){return jv(s,e)}function jv(s,e,i,r,l){Qt($r(),"useRoutes() may be used only in the context of a <Router> component.");let{navigator:c}=K.useContext(li),{matches:f}=K.useContext(Pi),p=f[f.length-1],m=p?p.params:{},d=p?p.pathname:"/",_=p?p.pathnameBase:"/",v=p&&p.route;{let T=v&&v.path||"";Wv(d,!v||T.endsWith("*")||T.endsWith("*?"),`You rendered descendant <Routes> (or called \`useRoutes()\`) at "${d}" (under <Route path="${T}">) but the parent route path has no trailing "*". This means if you navigate deeper, the parent won't match anymore and therefore the child routes will never render.

Please change the parent <Route path="${T}"> to <Route path="${T==="/"?"*":`${T}/*`}">.`)}let g=ms(),M;if(e){let T=typeof e=="string"?Qr(e):e;Qt(_==="/"||T.pathname?.startsWith(_),`When overriding the location using \`<Routes location>\` or \`useRoutes(routes, location)\`, the location pathname must begin with the portion of the URL pathname that was matched by all parent routes. The current pathname base is "${_}" but pathname "${T.pathname}" was given in the \`location\` prop.`),M=T}else M=g;let E=M.pathname||"/",R=E;if(_!=="/"){let T=_.replace(/^\//,"").split("/");R="/"+E.replace(/^\//,"").split("/").slice(T.length).join("/")}let x=Lv(s,{pathname:R});Oi(v||x!=null,`No routes matched location "${M.pathname}${M.search}${M.hash}" `),Oi(x==null||x[x.length-1].route.element!==void 0||x[x.length-1].route.Component!==void 0||x[x.length-1].route.lazy!==void 0,`Matched leaf route at location "${M.pathname}${M.search}${M.hash}" does not have an element or Component. This means it will render an <Outlet /> with a null value by default resulting in an "empty" page.`);let y=zM(x&&x.map(T=>Object.assign({},T,{params:Object.assign({},m,T.params),pathname:Ea([_,c.encodeLocation?c.encodeLocation(T.pathname.replace(/\?/g,"%3F").replace(/#/g,"%23")).pathname:T.pathname]),pathnameBase:T.pathnameBase==="/"?_:Ea([_,c.encodeLocation?c.encodeLocation(T.pathnameBase.replace(/\?/g,"%3F").replace(/#/g,"%23")).pathname:T.pathnameBase])})),f,i,r,l);return e&&y?K.createElement(ul.Provider,{value:{location:{pathname:"/",search:"",hash:"",state:null,key:"default",...M},navigationType:"POP"}},y):y}function OM(){let s=kM(),e=yM(s)?`${s.status} ${s.statusText}`:s instanceof Error?s.message:JSON.stringify(s),i=s instanceof Error?s.stack:null,r="rgba(200,200,200, 0.5)",l={padding:"0.5rem",backgroundColor:r},c={padding:"2px 4px",backgroundColor:r},f=null;return console.error("Error handled by React Router default ErrorBoundary:",s),f=K.createElement(K.Fragment,null,K.createElement("p",null,"💿 Hey developer 👋"),K.createElement("p",null,"You can provide a way better UX than this when your app throws errors by providing your own ",K.createElement("code",{style:c},"ErrorBoundary")," or"," ",K.createElement("code",{style:c},"errorElement")," prop on your route.")),K.createElement(K.Fragment,null,K.createElement("h2",null,"Unexpected Application Error!"),K.createElement("h3",{style:{fontStyle:"italic"}},e),i?K.createElement("pre",{style:l},i):null,f)}var PM=K.createElement(OM,null),Xv=class extends K.Component{constructor(s){super(s),this.state={location:s.location,revalidation:s.revalidation,error:s.error}}static getDerivedStateFromError(s){return{error:s}}static getDerivedStateFromProps(s,e){return e.location!==s.location||e.revalidation!=="idle"&&s.revalidation==="idle"?{error:s.error,location:s.location,revalidation:s.revalidation}:{error:s.error!==void 0?s.error:e.error,location:e.location,revalidation:s.revalidation||e.revalidation}}componentDidCatch(s,e){this.props.onError?this.props.onError(s,e):console.error("React Router caught the following error during render",s)}render(){let s=this.state.error;if(this.context&&typeof s=="object"&&s&&"digest"in s&&typeof s.digest=="string"){const i=wM(s.digest);i&&(s=i)}let e=s!==void 0?K.createElement(Pi.Provider,{value:this.props.routeContext},K.createElement(gp.Provider,{value:s,children:this.props.component})):this.props.children;return this.context?K.createElement(FM,{error:s},e):e}};Xv.contextType=EM;var Ph=new WeakMap;function FM({children:s,error:e}){let{basename:i}=K.useContext(li);if(typeof e=="object"&&e&&"digest"in e&&typeof e.digest=="string"){let r=CM(e.digest);if(r){let l=Ph.get(e);if(l)throw l;let c=Iv(r.location,i);if(Fv&&!Ph.get(e))if(c.isExternal||r.reloadDocument)window.location.href=c.absoluteURL||c.to;else{const f=Promise.resolve().then(()=>window.__reactRouterDataRouter.navigate(c.to,{replace:r.replace}));throw Ph.set(e,f),f}return K.createElement("meta",{httpEquiv:"refresh",content:`0;url=${c.absoluteURL||c.to}`})}}return s}function IM({routeContext:s,match:e,children:i}){let r=K.useContext(Jr);return r&&r.static&&r.staticContext&&(e.route.errorElement||e.route.ErrorBoundary)&&(r.staticContext._deepestRenderedBoundaryId=e.route.id),K.createElement(Pi.Provider,{value:s},i)}function zM(s,e=[],i=null,r=null,l=null){if(s==null){if(!i)return null;if(i.errors)s=i.matches;else if(e.length===0&&!i.initialized&&i.matches.length>0)s=i.matches;else return null}let c=s,f=i?.errors;if(f!=null){let _=c.findIndex(v=>v.route.id&&f?.[v.route.id]!==void 0);Qt(_>=0,`Could not find a matching route for errors on route IDs: ${Object.keys(f).join(",")}`),c=c.slice(0,Math.min(c.length,_+1))}let p=!1,m=-1;if(i)for(let _=0;_<c.length;_++){let v=c[_];if((v.route.HydrateFallback||v.route.hydrateFallbackElement)&&(m=_),v.route.id){let{loaderData:g,errors:M}=i,E=v.route.loader&&!g.hasOwnProperty(v.route.id)&&(!M||M[v.route.id]===void 0);if(v.route.lazy||E){p=!0,m>=0?c=c.slice(0,m+1):c=[c[0]];break}}}let d=i&&r?(_,v)=>{r(_,{location:i.location,params:i.matches?.[0]?.params??{},unstable_pattern:SM(i.matches),errorInfo:v})}:void 0;return c.reduceRight((_,v,g)=>{let M,E=!1,R=null,x=null;i&&(M=f&&v.route.id?f[v.route.id]:void 0,R=v.route.errorElement||PM,p&&(m<0&&g===0?(Wv("route-fallback",!1,"No `HydrateFallback` element provided to render during initial hydration"),E=!0,x=null):m===g&&(E=!0,x=v.route.hydrateFallbackElement||null)));let y=e.concat(c.slice(0,g+1)),T=()=>{let U;return M?U=R:E?U=x:v.route.Component?U=K.createElement(v.route.Component,null):v.route.element?U=v.route.element:U=_,K.createElement(IM,{match:v,routeContext:{outlet:_,matches:y,isDataRoute:i!=null},children:U})};return i&&(v.route.ErrorBoundary||v.route.errorElement||g===0)?K.createElement(Xv,{location:i.location,revalidation:i.revalidation,component:R,error:M,children:T(),routeContext:{outlet:null,matches:y,isDataRoute:!0},onError:d}):T()},null)}function _p(s){return`${s} must be used within a data router.  See https://reactrouter.com/en/main/routers/picking-a-router.`}function BM(s){let e=K.useContext(Jr);return Qt(e,_p(s)),e}function HM(s){let e=K.useContext(gu);return Qt(e,_p(s)),e}function GM(s){let e=K.useContext(Pi);return Qt(e,_p(s)),e}function vp(s){let e=GM(s),i=e.matches[e.matches.length-1];return Qt(i.route.id,`${s} can only be used on routes that contain a unique "id"`),i.route.id}function VM(){return vp("useRouteId")}function kM(){let s=K.useContext(gp),e=HM("useRouteError"),i=vp("useRouteError");return s!==void 0?s:e.errors?.[i]}function jM(){let{router:s}=BM("useNavigate"),e=vp("useNavigate"),i=K.useRef(!1);return Vv(()=>{i.current=!0}),K.useCallback(async(l,c={})=>{Oi(i.current,Gv),i.current&&(typeof l=="number"?await s.navigate(l):await s.navigate(l,{fromRouteId:e,...c}))},[s,e])}var A0={};function Wv(s,e,i){!e&&!A0[s]&&(A0[s]=!0,Oi(!1,i))}K.memo(XM);function XM({routes:s,future:e,state:i,onError:r}){return jv(s,void 0,i,r,e)}function WM({to:s,replace:e,state:i,relative:r}){Qt($r(),"<Navigate> may be used only in the context of a <Router> component.");let{static:l}=K.useContext(li);Oi(!l,"<Navigate> must not be used on the initial render in a <StaticRouter>. This is a no-op, but you should modify your code so the <Navigate> is only ever rendered in response to some user interaction or state change.");let{matches:c}=K.useContext(Pi),{pathname:f}=ms(),p=kv(),m=mp(s,pp(c),f,r==="path"),d=JSON.stringify(m);return K.useEffect(()=>{p(JSON.parse(d),{replace:e,state:i,relative:r})},[p,d,r,e,i]),null}function tl(s){Qt(!1,"A <Route> is only ever to be used as the child of <Routes> element, never rendered directly. Please wrap your <Route> in a <Routes>.")}function qM({basename:s="/",children:e=null,location:i,navigationType:r="POP",navigator:l,static:c=!1,unstable_useTransitions:f}){Qt(!$r(),"You cannot render a <Router> inside another <Router>. You should never have more than one in your app.");let p=s.replace(/^\/*/,"/"),m=K.useMemo(()=>({basename:p,navigator:l,static:c,unstable_useTransitions:f,future:{}}),[p,l,c,f]);typeof i=="string"&&(i=Qr(i));let{pathname:d="/",search:_="",hash:v="",state:g=null,key:M="default"}=i,E=K.useMemo(()=>{let R=Ra(d,p);return R==null?null:{location:{pathname:R,search:_,hash:v,state:g,key:M},navigationType:r}},[p,d,_,v,g,M,r]);return Oi(E!=null,`<Router basename="${p}"> is not able to match the URL "${d}${_}${v}" because it does not start with the basename, so the <Router> won't render anything.`),E==null?null:K.createElement(li.Provider,{value:m},K.createElement(ul.Provider,{children:e,value:E}))}function YM({children:s,location:e}){return LM(_d(s),e)}function _d(s,e=[]){let i=[];return K.Children.forEach(s,(r,l)=>{if(!K.isValidElement(r))return;let c=[...e,l];if(r.type===K.Fragment){i.push.apply(i,_d(r.props.children,c));return}Qt(r.type===tl,`[${typeof r.type=="string"?r.type:r.type.name}] is not a <Route> component. All component children of <Routes> must be a <Route> or <React.Fragment>`),Qt(!r.props.index||!r.props.children,"An index route cannot have child routes.");let f={id:r.props.id||c.join("-"),caseSensitive:r.props.caseSensitive,element:r.props.element,Component:r.props.Component,index:r.props.index,path:r.props.path,middleware:r.props.middleware,loader:r.props.loader,action:r.props.action,hydrateFallbackElement:r.props.hydrateFallbackElement,HydrateFallback:r.props.HydrateFallback,errorElement:r.props.errorElement,ErrorBoundary:r.props.ErrorBoundary,hasErrorBoundary:r.props.hasErrorBoundary===!0||r.props.ErrorBoundary!=null||r.props.errorElement!=null,shouldRevalidate:r.props.shouldRevalidate,handle:r.props.handle,lazy:r.props.lazy};r.props.children&&(f.children=_d(r.props.children,c)),i.push(f)}),i}var nu="get",iu="application/x-www-form-urlencoded";function _u(s){return typeof HTMLElement<"u"&&s instanceof HTMLElement}function ZM(s){return _u(s)&&s.tagName.toLowerCase()==="button"}function KM(s){return _u(s)&&s.tagName.toLowerCase()==="form"}function QM(s){return _u(s)&&s.tagName.toLowerCase()==="input"}function JM(s){return!!(s.metaKey||s.altKey||s.ctrlKey||s.shiftKey)}function $M(s,e){return s.button===0&&(!e||e==="_self")&&!JM(s)}var wc=null;function eE(){if(wc===null)try{new FormData(document.createElement("form"),0),wc=!1}catch{wc=!0}return wc}var tE=new Set(["application/x-www-form-urlencoded","multipart/form-data","text/plain"]);function Fh(s){return s!=null&&!tE.has(s)?(Oi(!1,`"${s}" is not a valid \`encType\` for \`<Form>\`/\`<fetcher.Form>\` and will default to "${iu}"`),null):s}function nE(s,e){let i,r,l,c,f;if(KM(s)){let p=s.getAttribute("action");r=p?Ra(p,e):null,i=s.getAttribute("method")||nu,l=Fh(s.getAttribute("enctype"))||iu,c=new FormData(s)}else if(ZM(s)||QM(s)&&(s.type==="submit"||s.type==="image")){let p=s.form;if(p==null)throw new Error('Cannot submit a <button> or <input type="submit"> without a <form>');let m=s.getAttribute("formaction")||p.getAttribute("action");if(r=m?Ra(m,e):null,i=s.getAttribute("formmethod")||p.getAttribute("method")||nu,l=Fh(s.getAttribute("formenctype"))||Fh(p.getAttribute("enctype"))||iu,c=new FormData(p,s),!eE()){let{name:d,type:_,value:v}=s;if(_==="image"){let g=d?`${d}.`:"";c.append(`${g}x`,"0"),c.append(`${g}y`,"0")}else d&&c.append(d,v)}}else{if(_u(s))throw new Error('Cannot submit element that is not <form>, <button>, or <input type="submit|image">');i=nu,r=null,l=iu,f=s}return c&&l==="text/plain"&&(f=c,c=void 0),{action:r,method:i.toLowerCase(),encType:l,formData:c,body:f}}Object.getOwnPropertyNames(Object.prototype).sort().join("\0");function xp(s,e){if(s===!1||s===null||typeof s>"u")throw new Error(e)}function iE(s,e,i,r){let l=typeof s=="string"?new URL(s,typeof window>"u"?"server://singlefetch/":window.location.origin):s;return i?l.pathname.endsWith("/")?l.pathname=`${l.pathname}_.${r}`:l.pathname=`${l.pathname}.${r}`:l.pathname==="/"?l.pathname=`_root.${r}`:e&&Ra(l.pathname,e)==="/"?l.pathname=`${e.replace(/\/$/,"")}/_root.${r}`:l.pathname=`${l.pathname.replace(/\/$/,"")}.${r}`,l}async function aE(s,e){if(s.id in e)return e[s.id];try{let i=await import(s.module);return e[s.id]=i,i}catch(i){return console.error(`Error loading route module \`${s.module}\`, reloading page...`),console.error(i),window.__reactRouterContext&&window.__reactRouterContext.isSpaMode,window.location.reload(),new Promise(()=>{})}}function sE(s){return s==null?!1:s.href==null?s.rel==="preload"&&typeof s.imageSrcSet=="string"&&typeof s.imageSizes=="string":typeof s.rel=="string"&&typeof s.href=="string"}async function rE(s,e,i){let r=await Promise.all(s.map(async l=>{let c=e.routes[l.route.id];if(c){let f=await aE(c,i);return f.links?f.links():[]}return[]}));return uE(r.flat(1).filter(sE).filter(l=>l.rel==="stylesheet"||l.rel==="preload").map(l=>l.rel==="stylesheet"?{...l,rel:"prefetch",as:"style"}:{...l,rel:"prefetch"}))}function R0(s,e,i,r,l,c){let f=(m,d)=>i[d]?m.route.id!==i[d].route.id:!0,p=(m,d)=>i[d].pathname!==m.pathname||i[d].route.path?.endsWith("*")&&i[d].params["*"]!==m.params["*"];return c==="assets"?e.filter((m,d)=>f(m,d)||p(m,d)):c==="data"?e.filter((m,d)=>{let _=r.routes[m.route.id];if(!_||!_.hasLoader)return!1;if(f(m,d)||p(m,d))return!0;if(m.route.shouldRevalidate){let v=m.route.shouldRevalidate({currentUrl:new URL(l.pathname+l.search+l.hash,window.origin),currentParams:i[0]?.params||{},nextUrl:new URL(s,window.origin),nextParams:m.params,defaultShouldRevalidate:!0});if(typeof v=="boolean")return v}return!0}):[]}function oE(s,e,{includeHydrateFallback:i}={}){return lE(s.map(r=>{let l=e.routes[r.route.id];if(!l)return[];let c=[l.module];return l.clientActionModule&&(c=c.concat(l.clientActionModule)),l.clientLoaderModule&&(c=c.concat(l.clientLoaderModule)),i&&l.hydrateFallbackModule&&(c=c.concat(l.hydrateFallbackModule)),l.imports&&(c=c.concat(l.imports)),c}).flat(1))}function lE(s){return[...new Set(s)]}function cE(s){let e={},i=Object.keys(s).sort();for(let r of i)e[r]=s[r];return e}function uE(s,e){let i=new Set;return new Set(e),s.reduce((r,l)=>{let c=JSON.stringify(cE(l));return i.has(c)||(i.add(c),r.push({key:c,link:l})),r},[])}function qv(){let s=K.useContext(Jr);return xp(s,"You must render this element inside a <DataRouterContext.Provider> element"),s}function fE(){let s=K.useContext(gu);return xp(s,"You must render this element inside a <DataRouterStateContext.Provider> element"),s}var yp=K.createContext(void 0);yp.displayName="FrameworkContext";function Yv(){let s=K.useContext(yp);return xp(s,"You must render this element inside a <HydratedRouter> element"),s}function hE(s,e){let i=K.useContext(yp),[r,l]=K.useState(!1),[c,f]=K.useState(!1),{onFocus:p,onBlur:m,onMouseEnter:d,onMouseLeave:_,onTouchStart:v}=e,g=K.useRef(null);K.useEffect(()=>{if(s==="render"&&f(!0),s==="viewport"){let R=y=>{y.forEach(T=>{f(T.isIntersecting)})},x=new IntersectionObserver(R,{threshold:.5});return g.current&&x.observe(g.current),()=>{x.disconnect()}}},[s]),K.useEffect(()=>{if(r){let R=setTimeout(()=>{f(!0)},100);return()=>{clearTimeout(R)}}},[r]);let M=()=>{l(!0)},E=()=>{l(!1),f(!1)};return i?s!=="intent"?[c,g,{}]:[c,g,{onFocus:qo(p,M),onBlur:qo(m,E),onMouseEnter:qo(d,M),onMouseLeave:qo(_,E),onTouchStart:qo(v,M)}]:[!1,g,{}]}function qo(s,e){return i=>{s&&s(i),i.defaultPrevented||e(i)}}function dE({page:s,...e}){let{router:i}=qv(),r=K.useMemo(()=>Lv(i.routes,s,i.basename),[i.routes,s,i.basename]);return r?K.createElement(mE,{page:s,matches:r,...e}):null}function pE(s){let{manifest:e,routeModules:i}=Yv(),[r,l]=K.useState([]);return K.useEffect(()=>{let c=!1;return rE(s,e,i).then(f=>{c||l(f)}),()=>{c=!0}},[s,e,i]),r}function mE({page:s,matches:e,...i}){let r=ms(),{future:l,manifest:c,routeModules:f}=Yv(),{basename:p}=qv(),{loaderData:m,matches:d}=fE(),_=K.useMemo(()=>R0(s,e,d,c,r,"data"),[s,e,d,c,r]),v=K.useMemo(()=>R0(s,e,d,c,r,"assets"),[s,e,d,c,r]),g=K.useMemo(()=>{if(s===r.pathname+r.search+r.hash)return[];let R=new Set,x=!1;if(e.forEach(T=>{let U=c.routes[T.route.id];!U||!U.hasLoader||(!_.some(P=>P.route.id===T.route.id)&&T.route.id in m&&f[T.route.id]?.shouldRevalidate||U.hasClientLoader?x=!0:R.add(T.route.id))}),R.size===0)return[];let y=iE(s,p,l.unstable_trailingSlashAwareDataRequests,"data");return x&&R.size>0&&y.searchParams.set("_routes",e.filter(T=>R.has(T.route.id)).map(T=>T.route.id).join(",")),[y.pathname+y.search]},[p,l.unstable_trailingSlashAwareDataRequests,m,r,c,_,e,s,f]),M=K.useMemo(()=>oE(v,c),[v,c]),E=pE(v);return K.createElement(K.Fragment,null,g.map(R=>K.createElement("link",{key:R,rel:"prefetch",as:"fetch",href:R,...i})),M.map(R=>K.createElement("link",{key:R,rel:"modulepreload",href:R,...i})),E.map(({key:R,link:x})=>K.createElement("link",{key:R,nonce:i.nonce,...x,crossOrigin:x.crossOrigin??i.crossOrigin})))}function gE(...s){return e=>{s.forEach(i=>{typeof i=="function"?i(e):i!=null&&(i.current=e)})}}var _E=typeof window<"u"&&typeof window.document<"u"&&typeof window.document.createElement<"u";try{_E&&(window.__reactRouterVersion="7.13.0")}catch{}function vE({basename:s,children:e,unstable_useTransitions:i,window:r}){let l=K.useRef();l.current==null&&(l.current=KS({window:r,v5Compat:!0}));let c=l.current,[f,p]=K.useState({action:c.action,location:c.location}),m=K.useCallback(d=>{i===!1?p(d):K.startTransition(()=>p(d))},[i]);return K.useLayoutEffect(()=>c.listen(m),[c,m]),K.createElement(qM,{basename:s,children:e,location:f.location,navigationType:f.action,navigator:c,unstable_useTransitions:i})}var Zv=/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i,rl=K.forwardRef(function({onClick:e,discover:i="render",prefetch:r="none",relative:l,reloadDocument:c,replace:f,state:p,target:m,to:d,preventScrollReset:_,viewTransition:v,unstable_defaultShouldRevalidate:g,...M},E){let{basename:R,unstable_useTransitions:x}=K.useContext(li),y=typeof d=="string"&&Zv.test(d),T=Iv(d,R);d=T.to;let U=DM(d,{relative:l}),[P,V,H]=hE(r,M),z=SE(d,{replace:f,state:p,target:m,preventScrollReset:_,relative:l,viewTransition:v,unstable_defaultShouldRevalidate:g,unstable_useTransitions:x});function A(pe){e&&e(pe),pe.defaultPrevented||z(pe)}let L=K.createElement("a",{...M,...H,href:T.absoluteURL||U,onClick:T.isExternal||c?e:A,ref:gE(E,V),target:m,"data-discover":!y&&i==="render"?"true":void 0});return P&&!y?K.createElement(K.Fragment,null,L,K.createElement(dE,{page:U})):L});rl.displayName="Link";var vd=K.forwardRef(function({"aria-current":e="page",caseSensitive:i=!1,className:r="",end:l=!1,style:c,to:f,viewTransition:p,children:m,...d},_){let v=fl(f,{relative:d.relative}),g=ms(),M=K.useContext(gu),{navigator:E,basename:R}=K.useContext(li),x=M!=null&&AE(v)&&p===!0,y=E.encodeLocation?E.encodeLocation(v).pathname:v.pathname,T=g.pathname,U=M&&M.navigation&&M.navigation.location?M.navigation.location.pathname:null;i||(T=T.toLowerCase(),U=U?U.toLowerCase():null,y=y.toLowerCase()),U&&R&&(U=Ra(U,R)||U);const P=y!=="/"&&y.endsWith("/")?y.length-1:y.length;let V=T===y||!l&&T.startsWith(y)&&T.charAt(P)==="/",H=U!=null&&(U===y||!l&&U.startsWith(y)&&U.charAt(y.length)==="/"),z={isActive:V,isPending:H,isTransitioning:x},A=V?e:void 0,L;typeof r=="function"?L=r(z):L=[r,V?"active":null,H?"pending":null,x?"transitioning":null].filter(Boolean).join(" ");let pe=typeof c=="function"?c(z):c;return K.createElement(rl,{...d,"aria-current":A,className:L,ref:_,style:pe,to:f,viewTransition:p},typeof m=="function"?m(z):m)});vd.displayName="NavLink";var xE=K.forwardRef(({discover:s="render",fetcherKey:e,navigate:i,reloadDocument:r,replace:l,state:c,method:f=nu,action:p,onSubmit:m,relative:d,preventScrollReset:_,viewTransition:v,unstable_defaultShouldRevalidate:g,...M},E)=>{let{unstable_useTransitions:R}=K.useContext(li),x=bE(),y=TE(p,{relative:d}),T=f.toLowerCase()==="get"?"get":"post",U=typeof p=="string"&&Zv.test(p),P=V=>{if(m&&m(V),V.defaultPrevented)return;V.preventDefault();let H=V.nativeEvent.submitter,z=H?.getAttribute("formmethod")||f,A=()=>x(H||V.currentTarget,{fetcherKey:e,method:z,navigate:i,replace:l,state:c,relative:d,preventScrollReset:_,viewTransition:v,unstable_defaultShouldRevalidate:g});R&&i!==!1?K.startTransition(()=>A()):A()};return K.createElement("form",{ref:E,method:T,action:y,onSubmit:r?m:P,...M,"data-discover":!U&&s==="render"?"true":void 0})});xE.displayName="Form";function yE(s){return`${s} must be used within a data router.  See https://reactrouter.com/en/main/routers/picking-a-router.`}function Kv(s){let e=K.useContext(Jr);return Qt(e,yE(s)),e}function SE(s,{target:e,replace:i,state:r,preventScrollReset:l,relative:c,viewTransition:f,unstable_defaultShouldRevalidate:p,unstable_useTransitions:m}={}){let d=kv(),_=ms(),v=fl(s,{relative:c});return K.useCallback(g=>{if($M(g,e)){g.preventDefault();let M=i!==void 0?i:sl(_)===sl(v),E=()=>d(s,{replace:M,state:r,preventScrollReset:l,relative:c,viewTransition:f,unstable_defaultShouldRevalidate:p});m?K.startTransition(()=>E()):E()}},[_,d,v,i,r,e,s,l,c,f,p,m])}var ME=0,EE=()=>`__${String(++ME)}__`;function bE(){let{router:s}=Kv("useSubmit"),{basename:e}=K.useContext(li),i=VM(),r=s.fetch,l=s.navigate;return K.useCallback(async(c,f={})=>{let{action:p,method:m,encType:d,formData:_,body:v}=nE(c,e);if(f.navigate===!1){let g=f.fetcherKey||EE();await r(g,i,f.action||p,{unstable_defaultShouldRevalidate:f.unstable_defaultShouldRevalidate,preventScrollReset:f.preventScrollReset,formData:_,body:v,formMethod:f.method||m,formEncType:f.encType||d,flushSync:f.flushSync})}else await l(f.action||p,{unstable_defaultShouldRevalidate:f.unstable_defaultShouldRevalidate,preventScrollReset:f.preventScrollReset,formData:_,body:v,formMethod:f.method||m,formEncType:f.encType||d,replace:f.replace,state:f.state,fromRouteId:i,flushSync:f.flushSync,viewTransition:f.viewTransition})},[r,l,e,i])}function TE(s,{relative:e}={}){let{basename:i}=K.useContext(li),r=K.useContext(Pi);Qt(r,"useFormAction must be used inside a RouteContext");let[l]=r.matches.slice(-1),c={...fl(s||".",{relative:e})},f=ms();if(s==null){c.search=f.search;let p=new URLSearchParams(c.search),m=p.getAll("index");if(m.some(_=>_==="")){p.delete("index"),m.filter(v=>v).forEach(v=>p.append("index",v));let _=p.toString();c.search=_?`?${_}`:""}}return(!s||s===".")&&l.route.index&&(c.search=c.search?c.search.replace(/^\?/,"?index&"):"?index"),i!=="/"&&(c.pathname=c.pathname==="/"?i:Ea([i,c.pathname])),sl(c)}function AE(s,{relative:e}={}){let i=K.useContext(Bv);Qt(i!=null,"`useViewTransitionState` must be used within `react-router-dom`'s `RouterProvider`.  Did you accidentally import `RouterProvider` from `react-router`?");let{basename:r}=Kv("useViewTransitionState"),l=fl(s,{relative:e});if(!i.isTransitioning)return!1;let c=Ra(i.currentLocation.pathname,r)||i.currentLocation.pathname,f=Ra(i.nextLocation.pathname,r)||i.nextLocation.pathname;return fu(l.pathname,f)!=null||fu(l.pathname,c)!=null}const C0="5050";function RE(){if(typeof window>"u")return`http://127.0.0.1:${C0}`;const{protocol:s,hostname:e}=window.location;return`${s}//${e}:${C0}`}const Qv=RE();function CE(s){return/^https?:\/\//i.test(s)?s:`${Qv}${s}`}async function Un(s,e){const i=await fetch(`${Qv}${s}`,{...e,headers:{"Content-Type":"application/json",...e?.headers??{}}});if(!i.ok){const r=await i.text();throw new Error(r||`HTTP ${i.status}`)}return await i.json()}function wE(s=!0){return Un(`/api/collections${s?"?include_stats=true":"?include_stats=false"}`)}function DE(s){return Un(`/api/collections/${encodeURIComponent(s)}`)}function NE(s,e){const i=new URLSearchParams;i.set("limit",String(e.limit)),e?.offset!=null&&i.set("offset",String(e.offset)),e?.query&&i.set("query",e.query);const r=i.toString()?`?${i.toString()}`:"";return Un(`/api/collections/${encodeURIComponent(s)}/embeddings-preview${r}`)}function UE(s,e){return Un(`/api/collections/${encodeURIComponent(s)}/search`,{method:"POST",body:JSON.stringify(e)})}function LE(s){return Un("/api/search/global",{method:"POST",body:JSON.stringify(s)})}function OE(s,e){return Un(`/api/collections/${encodeURIComponent(s)}/insert-text`,{method:"POST",body:JSON.stringify(e)})}function PE(s){return Un(`/api/collections/${encodeURIComponent(s)}/drop`,{method:"POST"})}function FE(){return Un("/api/backups/overview")}function IE(){return Un("/api/backups/start",{method:"POST"})}function zE(){return Un("/api/backups/stop",{method:"POST"})}function BE(s,e=180){return Un(`/api/backups/runs/${encodeURIComponent(s)}/logs?tail=${e}`)}function HE(s,e){return Un("/api/backups/schedule",{method:"POST",body:JSON.stringify({enabled:s,time_of_day:e})})}function GE(s){return Un("/api/backups/targets",{method:"POST",body:JSON.stringify(s)})}function VE(s,e){return Un(`/api/backups/targets/${encodeURIComponent(s)}`,{method:"PUT",body:JSON.stringify(e)})}function kE(s){return Un(`/api/backups/targets/${encodeURIComponent(s)}`,{method:"DELETE"})}function jE(s){return Un(`/api/backups/targets/${encodeURIComponent(s)}/backup`,{method:"POST"})}function _i(s){if(typeof s!="number"||Number.isNaN(s)||s<0)return"unknown";const e=["B","KB","MB","GB","TB","PB"];let i=s,r=0;for(;i>=1024&&r<e.length-1;)i/=1024,r+=1;return`${i.toFixed(i>=10||r===0?0:1)} ${e[r]}`}function XE(){const[s,e]=K.useState(null),[i,r]=K.useState(null),[l,c]=K.useState(null),[f,p]=K.useState(null),[m,d]=K.useState(!1),[_,v]=K.useState(!0),[g,M]=K.useState("02:00"),[E,R]=K.useState({profile:"nas",source:"",destination:""});async function x(){try{const w=await FE();e(w),v(w.schedule.enabled),M(w.schedule.time_of_day),p(null),!l&&w.recent_runs.length>0&&c(w.recent_runs[0].run_id)}catch(w){p(w instanceof Error?w.message:"Failed to fetch backup status.")}}async function y(w){try{const Y=await BE(w,180);r(Y),p(null)}catch(Y){p(Y instanceof Error?Y.message:"Failed to fetch backup logs.")}}async function T(){d(!0);try{await IE(),await x()}finally{d(!1)}}async function U(){d(!0);try{await zE(),await x()}finally{d(!1)}}async function P(){d(!0);try{await HE(_,g),await x()}catch(w){p(w instanceof Error?w.message:"Failed to update schedule.")}finally{d(!1)}}async function V(){if(!(!E.source.trim()||!E.destination.trim())){d(!0);try{await GE({profile:E.profile.trim()||"default",source:E.source.trim(),destination:E.destination.trim(),enabled:!0}),R({profile:"nas",source:"",destination:""}),await x()}catch(w){p(w instanceof Error?w.message:"Failed to add target.")}finally{d(!1)}}}async function H(w){d(!0);try{await VE(w.id,{enabled:!w.enabled}),await x()}catch(Y){p(Y instanceof Error?Y.message:"Failed to update target.")}finally{d(!1)}}async function z(w){if(confirm(`Delete target ${w.source} -> ${w.destination}?`)){d(!0);try{await kE(w.id),await x()}catch(Y){p(Y instanceof Error?Y.message:"Failed to delete target.")}finally{d(!1)}}}async function A(w){d(!0);try{await jE(w.id),await x()}catch(Y){p(Y instanceof Error?Y.message:"Failed to start target backup.")}finally{d(!1)}}K.useEffect(()=>{x()},[]),K.useEffect(()=>{const w=setInterval(()=>{x(),l&&y(l)},4e3);return()=>clearInterval(w)},[l]),K.useEffect(()=>{l&&y(l)},[l]);const L=K.useMemo(()=>s?.recent_runs.find(w=>w.run_id===l)??null,[s?.recent_runs,l]),pe=K.useMemo(()=>{const w=new Map;if(!s)return w;for(const Y of s.target_mappings)w.set(`${Y.profile}|${Y.source}|${Y.destination}`,Y);return w},[s]);return C.jsxs("section",{className:"backup-layout",children:[f&&C.jsx("div",{className:"error-banner",children:f}),s?C.jsxs(C.Fragment,{children:[C.jsxs("div",{className:"backup-header panel",children:[C.jsxs("div",{children:[C.jsx("h2",{children:"Backup"}),C.jsxs("p",{className:"muted",children:["Schedule: ",s.timer_schedule??"unknown"," · Pool: ",s.backup_pool??"unknown"," · Bandwidth:"," ",s.rsync_bwlimit??"unknown"]}),C.jsxs("div",{className:"health-pill",children:[C.jsx("span",{className:`status-dot ${s.storage_ready?"success":"warning"}`}),C.jsx("span",{children:s.storage_ready?"Storage ready":"Storage issues detected"})]})]}),C.jsx("div",{className:"inline-actions",children:s.status.running?C.jsx("button",{disabled:m,onClick:()=>{U()},children:"Stop Backup"}):C.jsx("button",{disabled:m,onClick:()=>{T()},children:"Start Backup"})})]}),C.jsxs("div",{className:"panel",children:[C.jsx("h3",{children:"Backup Scheduler"}),C.jsxs("div",{className:"schedule-form",children:[C.jsxs("label",{className:"schedule-toggle",children:[C.jsx("input",{type:"checkbox",checked:_,onChange:w=>v(w.target.checked)}),"Enabled"]}),C.jsxs("label",{children:["Time (UTC)",C.jsx("input",{type:"time",value:g,onChange:w=>M(w.target.value)})]}),C.jsx("button",{disabled:m,onClick:()=>{P()},children:"Save Schedule"})]}),C.jsxs("p",{className:"muted",children:["Next run: ",s.schedule.next_run_at?new Date(s.schedule.next_run_at).toLocaleString():"disabled"]}),C.jsxs("p",{className:"muted",children:["Last trigger:"," ",s.schedule.last_triggered_at?new Date(s.schedule.last_triggered_at).toLocaleString():"none"]})]}),C.jsxs("div",{className:"panel",children:[C.jsxs("p",{children:[C.jsx("strong",{children:"State:"})," ",s.status.running?"Running":"Idle"]}),s.status.started_at&&C.jsxs("p",{children:[C.jsx("strong",{children:"Started:"})," ",new Date(s.status.started_at).toLocaleString()]}),s.status.finished_at&&C.jsxs("p",{children:[C.jsx("strong",{children:"Finished:"})," ",new Date(s.status.finished_at).toLocaleString()]}),typeof s.status.exit_code=="number"&&C.jsxs("p",{children:[C.jsx("strong",{children:"Exit code:"})," ",s.status.exit_code]}),C.jsxs("p",{children:[C.jsx("strong",{children:"Progress:"})," ",s.status.progress_line??"No active progress line."]}),s.status.progress_total?C.jsxs("p",{children:[C.jsx("strong",{children:"Step Progress:"})," ",s.status.progress_current??0,"/",s.status.progress_total," ",s.status.active_step?`· ${s.status.active_step}`:""]}):null]}),C.jsxs("div",{className:"backup-grid",children:[C.jsxs("div",{className:"panel",children:[C.jsx("h3",{children:"Backup Targets & Destinations"}),C.jsx("div",{className:"target-health-list",children:s.target_health.map(w=>{const Y=pe.get(`${w.profile}|${w.source}|${w.destination}`);return C.jsxs("div",{className:"target-health-row",children:[C.jsxs("div",{className:"target-health-header",children:[C.jsx("strong",{children:w.source}),C.jsxs("div",{className:"inline-actions",children:[C.jsx("span",{className:w.ready?"health-badge ready":"health-badge issue",children:w.ready?"Ready":"Issue"}),Y&&C.jsxs(C.Fragment,{children:[C.jsx("button",{className:"tiny-button",disabled:m||s.status.running||!w.ready,title:s.status.running?"A backup is already running.":"Run backup for this target only",onClick:()=>{A(Y)},children:"Backup"}),C.jsx("button",{className:"tiny-button",onClick:()=>{H(Y)},children:Y.enabled?"Disable":"Enable"}),C.jsx("button",{className:"icon-danger-button",title:"Remove target",onClick:()=>{z(Y)},children:"×"})]})]})]}),C.jsx("p",{className:"muted",children:w.destination}),C.jsxs("p",{className:"muted",children:["Last backup: ",w.last_backup_at?new Date(w.last_backup_at).toLocaleString():"Never"]}),C.jsxs("div",{className:"target-health-meta",children:[C.jsx("span",{children:w.source_exists&&w.source_readable?"Source OK":"Source problem"}),C.jsx("span",{children:w.destination_exists&&w.destination_writable?"Destination writable":"Destination problem"}),C.jsx("span",{children:w.destination_separate_mount?"Mounted":"Not separate mount"})]})]},`${w.profile}:${w.source}`)})}),C.jsxs("details",{className:"add-target-details",children:[C.jsx("summary",{children:"Add Target"}),C.jsxs("div",{className:"schedule-form",style:{marginTop:10},children:[C.jsxs("label",{children:["Profile",C.jsx("input",{value:E.profile,onChange:w=>R({...E,profile:w.target.value})})]}),C.jsxs("label",{children:["Source",C.jsx("input",{value:E.source,onChange:w=>R({...E,source:w.target.value})})]}),C.jsxs("label",{children:["Destination",C.jsx("input",{value:E.destination,onChange:w=>R({...E,destination:w.target.value})})]}),C.jsx("button",{disabled:m,onClick:()=>{V()},children:"Add"})]})]})]}),C.jsxs("div",{className:"panel",children:[C.jsx("h3",{children:"Storage Health & Capacity"}),s.storage_diagnostics.filesystems.length>0&&C.jsxs(C.Fragment,{children:[C.jsx("h4",{children:"Disk usage (all mounts)"}),C.jsx("div",{className:"storage-df-table-wrap",children:C.jsxs("table",{className:"storage-df-table",children:[C.jsx("thead",{children:C.jsxs("tr",{children:[C.jsx("th",{children:"Filesystem"}),C.jsx("th",{children:"Mount"}),C.jsx("th",{children:"Used"}),C.jsx("th",{children:"Total"}),C.jsx("th",{children:"Free"}),C.jsx("th",{children:"Use%"})]})}),C.jsx("tbody",{children:s.storage_diagnostics.filesystems.map(w=>C.jsxs("tr",{children:[C.jsx("td",{className:"mono",children:w.filesystem}),C.jsx("td",{className:"mono",children:w.mount_point}),C.jsx("td",{children:_i(w.used_bytes)}),C.jsx("td",{children:_i(w.total_bytes)}),C.jsx("td",{children:_i(w.free_bytes)}),C.jsx("td",{children:w.used_percent!=null?`${w.used_percent}%`:"—"})]},`${w.filesystem}-${w.mount_point}`))})]})})]}),C.jsxs("div",{className:"storage-health-grid",children:[C.jsxs("div",{children:[C.jsx("h4",{children:"Sources"}),C.jsx("div",{className:"storage-list",children:s.storage_diagnostics.sources.map(w=>C.jsxs("div",{className:"storage-item",children:[C.jsxs("div",{className:"storage-item-head",children:[C.jsx("strong",{children:w.path}),C.jsx("span",{className:w.exists?"health-badge ready":"health-badge issue",children:w.exists?"Reachable":"Missing"})]}),C.jsxs("p",{className:"muted",children:["Used ",_i(w.used_bytes)," / ",_i(w.total_bytes)," (",w.used_percent??"?","%)"]}),C.jsxs("p",{className:"muted",children:["Free: ",_i(w.free_bytes)]}),C.jsxs("p",{className:"muted",children:["Mount: ",w.mount_point??"unknown"]})]},`source-${w.path}`))})]}),C.jsxs("div",{children:[C.jsx("h4",{children:"Destinations"}),C.jsx("div",{className:"storage-list",children:s.storage_diagnostics.destinations.map(w=>C.jsxs("div",{className:"storage-item",children:[C.jsxs("div",{className:"storage-item-head",children:[C.jsx("strong",{children:w.path}),C.jsx("span",{className:w.writable?"health-badge ready":"health-badge issue",children:w.writable?"Writable":"Not writable"})]}),C.jsxs("p",{className:"muted",children:["Used ",_i(w.used_bytes)," / ",_i(w.total_bytes)," (",w.used_percent??"?","%)"]}),C.jsxs("p",{className:"muted",children:["Free: ",_i(w.free_bytes)]}),C.jsxs("p",{className:"muted",children:["Mount: ",w.mount_point??"unknown"]})]},`dest-${w.path}`))})]})]}),C.jsxs("div",{className:"zfs-panel",children:[C.jsxs("div",{className:"storage-item-head",children:[C.jsx("h4",{children:"ZFS Status"}),C.jsx("span",{className:s.storage_diagnostics.zfs.status_ok===!1?"health-badge issue":"health-badge ready",children:s.storage_diagnostics.zfs.status_ok===!1?"Issue":"OK"})]}),C.jsxs("p",{className:"muted",children:["Pool: ",s.storage_diagnostics.zfs.pool??"unknown"," · Health: ",s.storage_diagnostics.zfs.health??"unknown"]}),C.jsxs("p",{className:"muted",children:["ZFS used ",_i(s.storage_diagnostics.zfs.used_bytes)," / available"," ",_i(s.storage_diagnostics.zfs.avail_bytes)]}),s.storage_diagnostics.zfs.status_summary&&C.jsx("p",{className:"muted",children:s.storage_diagnostics.zfs.status_summary}),s.storage_diagnostics.zfs.command_error&&C.jsx("p",{className:"muted",children:s.storage_diagnostics.zfs.command_error}),s.storage_diagnostics.zfs.errors.length>0&&C.jsx("div",{className:"storage-errors",children:s.storage_diagnostics.zfs.errors.map((w,Y)=>C.jsx("p",{children:w},`${w}-${Y}`))})]})]})]}),C.jsxs("div",{className:"panel",children:[C.jsx("h3",{children:"Recent Runs"}),C.jsx("div",{className:"run-list",children:s.recent_runs.map(w=>C.jsxs("button",{className:l===w.run_id?"active":"",onClick:()=>c(w.run_id),children:[C.jsx("span",{children:w.run_id}),C.jsx("span",{className:`run-status-badge ${w.status??"unknown"}`,children:w.status??"unknown"}),C.jsxs("span",{className:"muted",children:["archive: ",w.archive_ok===!0?"ok":w.archive_ok===!1?"failed":"unknown"," · sync failed:"," ",w.sync_failed??"?","/",w.sync_total??"?"]}),C.jsx("span",{className:"muted",children:w.last_line??"No summary line."})]},w.run_id))})]}),C.jsxs("div",{className:"panel",children:[C.jsxs("h3",{children:["Run Outcome ",L?`· ${L.run_id}`:""]}),i?.summary?C.jsxs("div",{className:"run-outcome-grid",children:[C.jsxs("p",{children:[C.jsx("strong",{children:"Status:"})," ",i.summary.status]}),C.jsxs("p",{children:[C.jsx("strong",{children:"Archive:"})," ",i.summary.include_archive===!1?"Skipped (target-only run)":i.summary.archive_ok?"OK":"Failed"," ",i.summary.archive_file?`(${i.summary.archive_file})`:""]}),C.jsxs("p",{children:[C.jsx("strong",{children:"Sync:"})," ",i.summary.sync_ok,"/",i.summary.sync_total," OK, ",i.summary.sync_failed," failed"]}),C.jsxs("p",{children:[C.jsx("strong",{children:"Snapshot:"})," ",i.summary.snapshot_status??"skipped"]}),i.summary.errors&&i.summary.errors.length>0&&C.jsx("div",{className:"storage-errors",children:i.summary.errors.map((w,Y)=>C.jsx("p",{children:w},`${w}-${Y}`))}),i.summary.sync_results?.length>0&&C.jsx("div",{className:"run-list",children:i.summary.sync_results.map(w=>C.jsxs("div",{className:"snapshot-row",children:[C.jsxs("span",{children:[w.source," → ",w.destination]}),C.jsx("span",{className:w.ok?"health-badge ready":"health-badge issue",children:w.ok?"OK":`exit ${w.exit_code}`})]},`${w.source}-${w.destination}`))})]}):C.jsx("p",{className:"muted",children:"No structured summary found for this run yet."})]}),C.jsxs("div",{className:"panel",children:[C.jsx("h3",{children:"Snapshot History"}),s.snapshots.length===0?C.jsx("p",{className:"muted",children:"No snapshots parsed yet."}):C.jsx("div",{className:"run-list",children:s.snapshots.map(w=>C.jsxs("div",{className:"snapshot-row",children:[C.jsx("span",{children:w.name}),C.jsx("span",{className:"muted",children:w.timestamp})]},`${w.name}-${w.timestamp}`))})]}),C.jsxs("div",{className:"panel",children:[C.jsx("h3",{children:"Backup Files"}),s.backup_files.length===0?C.jsx("p",{className:"muted",children:"No backups created yet."}):C.jsx("div",{className:"run-list",children:s.backup_files.map(w=>C.jsxs("a",{href:CE(`/api/backups/files/${encodeURIComponent(w.name)}`),className:"snapshot-row",children:[C.jsx("span",{className:"mono",children:w.name}),C.jsxs("span",{className:"muted",children:[_i(w.bytes)," · ",new Date(w.modified_at).toLocaleString()]})]},w.name))})]}),C.jsxs("div",{className:"panel",children:[C.jsxs("h3",{children:["Run Logs ",L?`· ${L.run_id}`:""]}),C.jsxs("div",{className:"backup-log-grid",children:[C.jsxs("div",{children:[C.jsx("h4",{children:"Main"}),C.jsx("pre",{className:"terminal",children:i?.main_log_tail||"No log content."})]}),C.jsxs("div",{children:[C.jsx("h4",{children:"Debug"}),C.jsx("pre",{className:"terminal",children:i?.debug_log_tail||"No log content."})]})]})]})]}):C.jsx("div",{className:"muted",children:"Loading backup status…"})]})}const Sp="183",kr={ROTATE:0,DOLLY:1,PAN:2},Vr={ROTATE:0,PAN:1,DOLLY_PAN:2,DOLLY_ROTATE:3},WE=0,w0=1,qE=2,au=1,YE=2,nl=3,ds=0,Zn=1,Sa=2,ba=0,jr=1,D0=2,N0=3,U0=4,ZE=5,Hs=100,KE=101,QE=102,JE=103,$E=104,eb=200,tb=201,nb=202,ib=203,xd=204,yd=205,ab=206,sb=207,rb=208,ob=209,lb=210,cb=211,ub=212,fb=213,hb=214,Sd=0,Md=1,Ed=2,Wr=3,bd=4,Td=5,Ad=6,Rd=7,Jv=0,db=1,pb=2,qi=0,$v=1,ex=2,tx=3,nx=4,ix=5,ax=6,sx=7,rx=300,js=301,qr=302,Ih=303,zh=304,vu=306,Cd=1e3,Ma=1001,wd=1002,Rn=1003,mb=1004,Dc=1005,Nn=1006,Bh=1007,Vs=1008,Si=1009,ox=1010,lx=1011,ol=1012,Mp=1013,Zi=1014,Xi=1015,Ca=1016,Ep=1017,bp=1018,ll=1020,cx=35902,ux=35899,fx=1021,hx=1022,Li=1023,wa=1026,ks=1027,dx=1028,Tp=1029,Yr=1030,Ap=1031,Rp=1033,su=33776,ru=33777,ou=33778,lu=33779,Dd=35840,Nd=35841,Ud=35842,Ld=35843,Od=36196,Pd=37492,Fd=37496,Id=37488,zd=37489,Bd=37490,Hd=37491,Gd=37808,Vd=37809,kd=37810,jd=37811,Xd=37812,Wd=37813,qd=37814,Yd=37815,Zd=37816,Kd=37817,Qd=37818,Jd=37819,$d=37820,ep=37821,tp=36492,np=36494,ip=36495,ap=36283,sp=36284,rp=36285,op=36286,gb=3200,_b=0,vb=1,fs="",xi="srgb",Zr="srgb-linear",hu="linear",Bt="srgb",Cr=7680,L0=519,xb=512,yb=513,Sb=514,Cp=515,Mb=516,Eb=517,wp=518,bb=519,O0=35044,P0="300 es",Wi=2e3,du=2001;function Tb(s){for(let e=s.length-1;e>=0;--e)if(s[e]>=65535)return!0;return!1}function pu(s){return document.createElementNS("http://www.w3.org/1999/xhtml",s)}function Ab(){const s=pu("canvas");return s.style.display="block",s}const F0={};function I0(...s){const e="THREE."+s.shift();console.log(e,...s)}function px(s){const e=s[0];if(typeof e=="string"&&e.startsWith("TSL:")){const i=s[1];i&&i.isStackTrace?s[0]+=" "+i.getLocation():s[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return s}function st(...s){s=px(s);const e="THREE."+s.shift();{const i=s[0];i&&i.isStackTrace?console.warn(i.getError(e)):console.warn(e,...s)}}function At(...s){s=px(s);const e="THREE."+s.shift();{const i=s[0];i&&i.isStackTrace?console.error(i.getError(e)):console.error(e,...s)}}function mu(...s){const e=s.join(" ");e in F0||(F0[e]=!0,st(...s))}function Rb(s,e,i){return new Promise(function(r,l){function c(){switch(s.clientWaitSync(e,s.SYNC_FLUSH_COMMANDS_BIT,0)){case s.WAIT_FAILED:l();break;case s.TIMEOUT_EXPIRED:setTimeout(c,i);break;default:r()}}setTimeout(c,i)})}const Cb={[Sd]:Md,[Ed]:Ad,[bd]:Rd,[Wr]:Td,[Md]:Sd,[Ad]:Ed,[Rd]:bd,[Td]:Wr};class Xs{addEventListener(e,i){this._listeners===void 0&&(this._listeners={});const r=this._listeners;r[e]===void 0&&(r[e]=[]),r[e].indexOf(i)===-1&&r[e].push(i)}hasEventListener(e,i){const r=this._listeners;return r===void 0?!1:r[e]!==void 0&&r[e].indexOf(i)!==-1}removeEventListener(e,i){const r=this._listeners;if(r===void 0)return;const l=r[e];if(l!==void 0){const c=l.indexOf(i);c!==-1&&l.splice(c,1)}}dispatchEvent(e){const i=this._listeners;if(i===void 0)return;const r=i[e.type];if(r!==void 0){e.target=this;const l=r.slice(0);for(let c=0,f=l.length;c<f;c++)l[c].call(this,e);e.target=null}}}const wn=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],cu=Math.PI/180,lp=180/Math.PI;function hl(){const s=Math.random()*4294967295|0,e=Math.random()*4294967295|0,i=Math.random()*4294967295|0,r=Math.random()*4294967295|0;return(wn[s&255]+wn[s>>8&255]+wn[s>>16&255]+wn[s>>24&255]+"-"+wn[e&255]+wn[e>>8&255]+"-"+wn[e>>16&15|64]+wn[e>>24&255]+"-"+wn[i&63|128]+wn[i>>8&255]+"-"+wn[i>>16&255]+wn[i>>24&255]+wn[r&255]+wn[r>>8&255]+wn[r>>16&255]+wn[r>>24&255]).toLowerCase()}function xt(s,e,i){return Math.max(e,Math.min(i,s))}function wb(s,e){return(s%e+e)%e}function Hh(s,e,i){return(1-i)*s+i*e}function Yo(s,e){switch(e.constructor){case Float32Array:return s;case Uint32Array:return s/4294967295;case Uint16Array:return s/65535;case Uint8Array:return s/255;case Int32Array:return Math.max(s/2147483647,-1);case Int16Array:return Math.max(s/32767,-1);case Int8Array:return Math.max(s/127,-1);default:throw new Error("Invalid component type.")}}function Wn(s,e){switch(e.constructor){case Float32Array:return s;case Uint32Array:return Math.round(s*4294967295);case Uint16Array:return Math.round(s*65535);case Uint8Array:return Math.round(s*255);case Int32Array:return Math.round(s*2147483647);case Int16Array:return Math.round(s*32767);case Int8Array:return Math.round(s*127);default:throw new Error("Invalid component type.")}}const Db={DEG2RAD:cu};class mt{constructor(e=0,i=0){mt.prototype.isVector2=!0,this.x=e,this.y=i}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,i){return this.x=e,this.y=i,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,i){switch(e){case 0:this.x=i;break;case 1:this.y=i;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,i){return this.x=e.x+i.x,this.y=e.y+i.y,this}addScaledVector(e,i){return this.x+=e.x*i,this.y+=e.y*i,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,i){return this.x=e.x-i.x,this.y=e.y-i.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){const i=this.x,r=this.y,l=e.elements;return this.x=l[0]*i+l[3]*r+l[6],this.y=l[1]*i+l[4]*r+l[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,i){return this.x=xt(this.x,e.x,i.x),this.y=xt(this.y,e.y,i.y),this}clampScalar(e,i){return this.x=xt(this.x,e,i),this.y=xt(this.y,e,i),this}clampLength(e,i){const r=this.length();return this.divideScalar(r||1).multiplyScalar(xt(r,e,i))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){const i=Math.sqrt(this.lengthSq()*e.lengthSq());if(i===0)return Math.PI/2;const r=this.dot(e)/i;return Math.acos(xt(r,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const i=this.x-e.x,r=this.y-e.y;return i*i+r*r}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,i){return this.x+=(e.x-this.x)*i,this.y+=(e.y-this.y)*i,this}lerpVectors(e,i,r){return this.x=e.x+(i.x-e.x)*r,this.y=e.y+(i.y-e.y)*r,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,i=0){return this.x=e[i],this.y=e[i+1],this}toArray(e=[],i=0){return e[i]=this.x,e[i+1]=this.y,e}fromBufferAttribute(e,i){return this.x=e.getX(i),this.y=e.getY(i),this}rotateAround(e,i){const r=Math.cos(i),l=Math.sin(i),c=this.x-e.x,f=this.y-e.y;return this.x=c*r-f*l+e.x,this.y=c*l+f*r+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}}class ps{constructor(e=0,i=0,r=0,l=1){this.isQuaternion=!0,this._x=e,this._y=i,this._z=r,this._w=l}static slerpFlat(e,i,r,l,c,f,p){let m=r[l+0],d=r[l+1],_=r[l+2],v=r[l+3],g=c[f+0],M=c[f+1],E=c[f+2],R=c[f+3];if(v!==R||m!==g||d!==M||_!==E){let x=m*g+d*M+_*E+v*R;x<0&&(g=-g,M=-M,E=-E,R=-R,x=-x);let y=1-p;if(x<.9995){const T=Math.acos(x),U=Math.sin(T);y=Math.sin(y*T)/U,p=Math.sin(p*T)/U,m=m*y+g*p,d=d*y+M*p,_=_*y+E*p,v=v*y+R*p}else{m=m*y+g*p,d=d*y+M*p,_=_*y+E*p,v=v*y+R*p;const T=1/Math.sqrt(m*m+d*d+_*_+v*v);m*=T,d*=T,_*=T,v*=T}}e[i]=m,e[i+1]=d,e[i+2]=_,e[i+3]=v}static multiplyQuaternionsFlat(e,i,r,l,c,f){const p=r[l],m=r[l+1],d=r[l+2],_=r[l+3],v=c[f],g=c[f+1],M=c[f+2],E=c[f+3];return e[i]=p*E+_*v+m*M-d*g,e[i+1]=m*E+_*g+d*v-p*M,e[i+2]=d*E+_*M+p*g-m*v,e[i+3]=_*E-p*v-m*g-d*M,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,i,r,l){return this._x=e,this._y=i,this._z=r,this._w=l,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,i=!0){const r=e._x,l=e._y,c=e._z,f=e._order,p=Math.cos,m=Math.sin,d=p(r/2),_=p(l/2),v=p(c/2),g=m(r/2),M=m(l/2),E=m(c/2);switch(f){case"XYZ":this._x=g*_*v+d*M*E,this._y=d*M*v-g*_*E,this._z=d*_*E+g*M*v,this._w=d*_*v-g*M*E;break;case"YXZ":this._x=g*_*v+d*M*E,this._y=d*M*v-g*_*E,this._z=d*_*E-g*M*v,this._w=d*_*v+g*M*E;break;case"ZXY":this._x=g*_*v-d*M*E,this._y=d*M*v+g*_*E,this._z=d*_*E+g*M*v,this._w=d*_*v-g*M*E;break;case"ZYX":this._x=g*_*v-d*M*E,this._y=d*M*v+g*_*E,this._z=d*_*E-g*M*v,this._w=d*_*v+g*M*E;break;case"YZX":this._x=g*_*v+d*M*E,this._y=d*M*v+g*_*E,this._z=d*_*E-g*M*v,this._w=d*_*v-g*M*E;break;case"XZY":this._x=g*_*v-d*M*E,this._y=d*M*v-g*_*E,this._z=d*_*E+g*M*v,this._w=d*_*v+g*M*E;break;default:st("Quaternion: .setFromEuler() encountered an unknown order: "+f)}return i===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,i){const r=i/2,l=Math.sin(r);return this._x=e.x*l,this._y=e.y*l,this._z=e.z*l,this._w=Math.cos(r),this._onChangeCallback(),this}setFromRotationMatrix(e){const i=e.elements,r=i[0],l=i[4],c=i[8],f=i[1],p=i[5],m=i[9],d=i[2],_=i[6],v=i[10],g=r+p+v;if(g>0){const M=.5/Math.sqrt(g+1);this._w=.25/M,this._x=(_-m)*M,this._y=(c-d)*M,this._z=(f-l)*M}else if(r>p&&r>v){const M=2*Math.sqrt(1+r-p-v);this._w=(_-m)/M,this._x=.25*M,this._y=(l+f)/M,this._z=(c+d)/M}else if(p>v){const M=2*Math.sqrt(1+p-r-v);this._w=(c-d)/M,this._x=(l+f)/M,this._y=.25*M,this._z=(m+_)/M}else{const M=2*Math.sqrt(1+v-r-p);this._w=(f-l)/M,this._x=(c+d)/M,this._y=(m+_)/M,this._z=.25*M}return this._onChangeCallback(),this}setFromUnitVectors(e,i){let r=e.dot(i)+1;return r<1e-8?(r=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=r):(this._x=0,this._y=-e.z,this._z=e.y,this._w=r)):(this._x=e.y*i.z-e.z*i.y,this._y=e.z*i.x-e.x*i.z,this._z=e.x*i.y-e.y*i.x,this._w=r),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(xt(this.dot(e),-1,1)))}rotateTowards(e,i){const r=this.angleTo(e);if(r===0)return this;const l=Math.min(1,i/r);return this.slerp(e,l),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,i){const r=e._x,l=e._y,c=e._z,f=e._w,p=i._x,m=i._y,d=i._z,_=i._w;return this._x=r*_+f*p+l*d-c*m,this._y=l*_+f*m+c*p-r*d,this._z=c*_+f*d+r*m-l*p,this._w=f*_-r*p-l*m-c*d,this._onChangeCallback(),this}slerp(e,i){let r=e._x,l=e._y,c=e._z,f=e._w,p=this.dot(e);p<0&&(r=-r,l=-l,c=-c,f=-f,p=-p);let m=1-i;if(p<.9995){const d=Math.acos(p),_=Math.sin(d);m=Math.sin(m*d)/_,i=Math.sin(i*d)/_,this._x=this._x*m+r*i,this._y=this._y*m+l*i,this._z=this._z*m+c*i,this._w=this._w*m+f*i,this._onChangeCallback()}else this._x=this._x*m+r*i,this._y=this._y*m+l*i,this._z=this._z*m+c*i,this._w=this._w*m+f*i,this.normalize();return this}slerpQuaternions(e,i,r){return this.copy(e).slerp(i,r)}random(){const e=2*Math.PI*Math.random(),i=2*Math.PI*Math.random(),r=Math.random(),l=Math.sqrt(1-r),c=Math.sqrt(r);return this.set(l*Math.sin(e),l*Math.cos(e),c*Math.sin(i),c*Math.cos(i))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,i=0){return this._x=e[i],this._y=e[i+1],this._z=e[i+2],this._w=e[i+3],this._onChangeCallback(),this}toArray(e=[],i=0){return e[i]=this._x,e[i+1]=this._y,e[i+2]=this._z,e[i+3]=this._w,e}fromBufferAttribute(e,i){return this._x=e.getX(i),this._y=e.getY(i),this._z=e.getZ(i),this._w=e.getW(i),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}class se{constructor(e=0,i=0,r=0){se.prototype.isVector3=!0,this.x=e,this.y=i,this.z=r}set(e,i,r){return r===void 0&&(r=this.z),this.x=e,this.y=i,this.z=r,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,i){switch(e){case 0:this.x=i;break;case 1:this.y=i;break;case 2:this.z=i;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,i){return this.x=e.x+i.x,this.y=e.y+i.y,this.z=e.z+i.z,this}addScaledVector(e,i){return this.x+=e.x*i,this.y+=e.y*i,this.z+=e.z*i,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,i){return this.x=e.x-i.x,this.y=e.y-i.y,this.z=e.z-i.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,i){return this.x=e.x*i.x,this.y=e.y*i.y,this.z=e.z*i.z,this}applyEuler(e){return this.applyQuaternion(z0.setFromEuler(e))}applyAxisAngle(e,i){return this.applyQuaternion(z0.setFromAxisAngle(e,i))}applyMatrix3(e){const i=this.x,r=this.y,l=this.z,c=e.elements;return this.x=c[0]*i+c[3]*r+c[6]*l,this.y=c[1]*i+c[4]*r+c[7]*l,this.z=c[2]*i+c[5]*r+c[8]*l,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){const i=this.x,r=this.y,l=this.z,c=e.elements,f=1/(c[3]*i+c[7]*r+c[11]*l+c[15]);return this.x=(c[0]*i+c[4]*r+c[8]*l+c[12])*f,this.y=(c[1]*i+c[5]*r+c[9]*l+c[13])*f,this.z=(c[2]*i+c[6]*r+c[10]*l+c[14])*f,this}applyQuaternion(e){const i=this.x,r=this.y,l=this.z,c=e.x,f=e.y,p=e.z,m=e.w,d=2*(f*l-p*r),_=2*(p*i-c*l),v=2*(c*r-f*i);return this.x=i+m*d+f*v-p*_,this.y=r+m*_+p*d-c*v,this.z=l+m*v+c*_-f*d,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){const i=this.x,r=this.y,l=this.z,c=e.elements;return this.x=c[0]*i+c[4]*r+c[8]*l,this.y=c[1]*i+c[5]*r+c[9]*l,this.z=c[2]*i+c[6]*r+c[10]*l,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,i){return this.x=xt(this.x,e.x,i.x),this.y=xt(this.y,e.y,i.y),this.z=xt(this.z,e.z,i.z),this}clampScalar(e,i){return this.x=xt(this.x,e,i),this.y=xt(this.y,e,i),this.z=xt(this.z,e,i),this}clampLength(e,i){const r=this.length();return this.divideScalar(r||1).multiplyScalar(xt(r,e,i))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,i){return this.x+=(e.x-this.x)*i,this.y+=(e.y-this.y)*i,this.z+=(e.z-this.z)*i,this}lerpVectors(e,i,r){return this.x=e.x+(i.x-e.x)*r,this.y=e.y+(i.y-e.y)*r,this.z=e.z+(i.z-e.z)*r,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,i){const r=e.x,l=e.y,c=e.z,f=i.x,p=i.y,m=i.z;return this.x=l*m-c*p,this.y=c*f-r*m,this.z=r*p-l*f,this}projectOnVector(e){const i=e.lengthSq();if(i===0)return this.set(0,0,0);const r=e.dot(this)/i;return this.copy(e).multiplyScalar(r)}projectOnPlane(e){return Gh.copy(this).projectOnVector(e),this.sub(Gh)}reflect(e){return this.sub(Gh.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){const i=Math.sqrt(this.lengthSq()*e.lengthSq());if(i===0)return Math.PI/2;const r=this.dot(e)/i;return Math.acos(xt(r,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const i=this.x-e.x,r=this.y-e.y,l=this.z-e.z;return i*i+r*r+l*l}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,i,r){const l=Math.sin(i)*e;return this.x=l*Math.sin(r),this.y=Math.cos(i)*e,this.z=l*Math.cos(r),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,i,r){return this.x=e*Math.sin(i),this.y=r,this.z=e*Math.cos(i),this}setFromMatrixPosition(e){const i=e.elements;return this.x=i[12],this.y=i[13],this.z=i[14],this}setFromMatrixScale(e){const i=this.setFromMatrixColumn(e,0).length(),r=this.setFromMatrixColumn(e,1).length(),l=this.setFromMatrixColumn(e,2).length();return this.x=i,this.y=r,this.z=l,this}setFromMatrixColumn(e,i){return this.fromArray(e.elements,i*4)}setFromMatrix3Column(e,i){return this.fromArray(e.elements,i*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,i=0){return this.x=e[i],this.y=e[i+1],this.z=e[i+2],this}toArray(e=[],i=0){return e[i]=this.x,e[i+1]=this.y,e[i+2]=this.z,e}fromBufferAttribute(e,i){return this.x=e.getX(i),this.y=e.getY(i),this.z=e.getZ(i),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){const e=Math.random()*Math.PI*2,i=Math.random()*2-1,r=Math.sqrt(1-i*i);return this.x=r*Math.cos(e),this.y=i,this.z=r*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}}const Gh=new se,z0=new ps;class dt{constructor(e,i,r,l,c,f,p,m,d){dt.prototype.isMatrix3=!0,this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,i,r,l,c,f,p,m,d)}set(e,i,r,l,c,f,p,m,d){const _=this.elements;return _[0]=e,_[1]=l,_[2]=p,_[3]=i,_[4]=c,_[5]=m,_[6]=r,_[7]=f,_[8]=d,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){const i=this.elements,r=e.elements;return i[0]=r[0],i[1]=r[1],i[2]=r[2],i[3]=r[3],i[4]=r[4],i[5]=r[5],i[6]=r[6],i[7]=r[7],i[8]=r[8],this}extractBasis(e,i,r){return e.setFromMatrix3Column(this,0),i.setFromMatrix3Column(this,1),r.setFromMatrix3Column(this,2),this}setFromMatrix4(e){const i=e.elements;return this.set(i[0],i[4],i[8],i[1],i[5],i[9],i[2],i[6],i[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,i){const r=e.elements,l=i.elements,c=this.elements,f=r[0],p=r[3],m=r[6],d=r[1],_=r[4],v=r[7],g=r[2],M=r[5],E=r[8],R=l[0],x=l[3],y=l[6],T=l[1],U=l[4],P=l[7],V=l[2],H=l[5],z=l[8];return c[0]=f*R+p*T+m*V,c[3]=f*x+p*U+m*H,c[6]=f*y+p*P+m*z,c[1]=d*R+_*T+v*V,c[4]=d*x+_*U+v*H,c[7]=d*y+_*P+v*z,c[2]=g*R+M*T+E*V,c[5]=g*x+M*U+E*H,c[8]=g*y+M*P+E*z,this}multiplyScalar(e){const i=this.elements;return i[0]*=e,i[3]*=e,i[6]*=e,i[1]*=e,i[4]*=e,i[7]*=e,i[2]*=e,i[5]*=e,i[8]*=e,this}determinant(){const e=this.elements,i=e[0],r=e[1],l=e[2],c=e[3],f=e[4],p=e[5],m=e[6],d=e[7],_=e[8];return i*f*_-i*p*d-r*c*_+r*p*m+l*c*d-l*f*m}invert(){const e=this.elements,i=e[0],r=e[1],l=e[2],c=e[3],f=e[4],p=e[5],m=e[6],d=e[7],_=e[8],v=_*f-p*d,g=p*m-_*c,M=d*c-f*m,E=i*v+r*g+l*M;if(E===0)return this.set(0,0,0,0,0,0,0,0,0);const R=1/E;return e[0]=v*R,e[1]=(l*d-_*r)*R,e[2]=(p*r-l*f)*R,e[3]=g*R,e[4]=(_*i-l*m)*R,e[5]=(l*c-p*i)*R,e[6]=M*R,e[7]=(r*m-d*i)*R,e[8]=(f*i-r*c)*R,this}transpose(){let e;const i=this.elements;return e=i[1],i[1]=i[3],i[3]=e,e=i[2],i[2]=i[6],i[6]=e,e=i[5],i[5]=i[7],i[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){const i=this.elements;return e[0]=i[0],e[1]=i[3],e[2]=i[6],e[3]=i[1],e[4]=i[4],e[5]=i[7],e[6]=i[2],e[7]=i[5],e[8]=i[8],this}setUvTransform(e,i,r,l,c,f,p){const m=Math.cos(c),d=Math.sin(c);return this.set(r*m,r*d,-r*(m*f+d*p)+f+e,-l*d,l*m,-l*(-d*f+m*p)+p+i,0,0,1),this}scale(e,i){return this.premultiply(Vh.makeScale(e,i)),this}rotate(e){return this.premultiply(Vh.makeRotation(-e)),this}translate(e,i){return this.premultiply(Vh.makeTranslation(e,i)),this}makeTranslation(e,i){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,i,0,0,1),this}makeRotation(e){const i=Math.cos(e),r=Math.sin(e);return this.set(i,-r,0,r,i,0,0,0,1),this}makeScale(e,i){return this.set(e,0,0,0,i,0,0,0,1),this}equals(e){const i=this.elements,r=e.elements;for(let l=0;l<9;l++)if(i[l]!==r[l])return!1;return!0}fromArray(e,i=0){for(let r=0;r<9;r++)this.elements[r]=e[r+i];return this}toArray(e=[],i=0){const r=this.elements;return e[i]=r[0],e[i+1]=r[1],e[i+2]=r[2],e[i+3]=r[3],e[i+4]=r[4],e[i+5]=r[5],e[i+6]=r[6],e[i+7]=r[7],e[i+8]=r[8],e}clone(){return new this.constructor().fromArray(this.elements)}}const Vh=new dt,B0=new dt().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),H0=new dt().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function Nb(){const s={enabled:!0,workingColorSpace:Zr,spaces:{},convert:function(l,c,f){return this.enabled===!1||c===f||!c||!f||(this.spaces[c].transfer===Bt&&(l.r=Ta(l.r),l.g=Ta(l.g),l.b=Ta(l.b)),this.spaces[c].primaries!==this.spaces[f].primaries&&(l.applyMatrix3(this.spaces[c].toXYZ),l.applyMatrix3(this.spaces[f].fromXYZ)),this.spaces[f].transfer===Bt&&(l.r=Xr(l.r),l.g=Xr(l.g),l.b=Xr(l.b))),l},workingToColorSpace:function(l,c){return this.convert(l,this.workingColorSpace,c)},colorSpaceToWorking:function(l,c){return this.convert(l,c,this.workingColorSpace)},getPrimaries:function(l){return this.spaces[l].primaries},getTransfer:function(l){return l===fs?hu:this.spaces[l].transfer},getToneMappingMode:function(l){return this.spaces[l].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(l,c=this.workingColorSpace){return l.fromArray(this.spaces[c].luminanceCoefficients)},define:function(l){Object.assign(this.spaces,l)},_getMatrix:function(l,c,f){return l.copy(this.spaces[c].toXYZ).multiply(this.spaces[f].fromXYZ)},_getDrawingBufferColorSpace:function(l){return this.spaces[l].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(l=this.workingColorSpace){return this.spaces[l].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(l,c){return mu("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),s.workingToColorSpace(l,c)},toWorkingColorSpace:function(l,c){return mu("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),s.colorSpaceToWorking(l,c)}},e=[.64,.33,.3,.6,.15,.06],i=[.2126,.7152,.0722],r=[.3127,.329];return s.define({[Zr]:{primaries:e,whitePoint:r,transfer:hu,toXYZ:B0,fromXYZ:H0,luminanceCoefficients:i,workingColorSpaceConfig:{unpackColorSpace:xi},outputColorSpaceConfig:{drawingBufferColorSpace:xi}},[xi]:{primaries:e,whitePoint:r,transfer:Bt,toXYZ:B0,fromXYZ:H0,luminanceCoefficients:i,outputColorSpaceConfig:{drawingBufferColorSpace:xi}}}),s}const Rt=Nb();function Ta(s){return s<.04045?s*.0773993808:Math.pow(s*.9478672986+.0521327014,2.4)}function Xr(s){return s<.0031308?s*12.92:1.055*Math.pow(s,.41666)-.055}let wr;class Ub{static getDataURL(e,i="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let r;if(e instanceof HTMLCanvasElement)r=e;else{wr===void 0&&(wr=pu("canvas")),wr.width=e.width,wr.height=e.height;const l=wr.getContext("2d");e instanceof ImageData?l.putImageData(e,0,0):l.drawImage(e,0,0,e.width,e.height),r=wr}return r.toDataURL(i)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){const i=pu("canvas");i.width=e.width,i.height=e.height;const r=i.getContext("2d");r.drawImage(e,0,0,e.width,e.height);const l=r.getImageData(0,0,e.width,e.height),c=l.data;for(let f=0;f<c.length;f++)c[f]=Ta(c[f]/255)*255;return r.putImageData(l,0,0),i}else if(e.data){const i=e.data.slice(0);for(let r=0;r<i.length;r++)i instanceof Uint8Array||i instanceof Uint8ClampedArray?i[r]=Math.floor(Ta(i[r]/255)*255):i[r]=Ta(i[r]);return{data:i,width:e.width,height:e.height}}else return st("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}}let Lb=0;class Dp{constructor(e=null){this.isSource=!0,Object.defineProperty(this,"id",{value:Lb++}),this.uuid=hl(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){const i=this.data;return typeof HTMLVideoElement<"u"&&i instanceof HTMLVideoElement?e.set(i.videoWidth,i.videoHeight,0):typeof VideoFrame<"u"&&i instanceof VideoFrame?e.set(i.displayHeight,i.displayWidth,0):i!==null?e.set(i.width,i.height,i.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){const i=e===void 0||typeof e=="string";if(!i&&e.images[this.uuid]!==void 0)return e.images[this.uuid];const r={uuid:this.uuid,url:""},l=this.data;if(l!==null){let c;if(Array.isArray(l)){c=[];for(let f=0,p=l.length;f<p;f++)l[f].isDataTexture?c.push(kh(l[f].image)):c.push(kh(l[f]))}else c=kh(l);r.url=c}return i||(e.images[this.uuid]=r),r}}function kh(s){return typeof HTMLImageElement<"u"&&s instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&s instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&s instanceof ImageBitmap?Ub.getDataURL(s):s.data?{data:Array.from(s.data),width:s.width,height:s.height,type:s.data.constructor.name}:(st("Texture: Unable to serialize Texture."),{})}let Ob=0;const jh=new se;class Bn extends Xs{constructor(e=Bn.DEFAULT_IMAGE,i=Bn.DEFAULT_MAPPING,r=Ma,l=Ma,c=Nn,f=Vs,p=Li,m=Si,d=Bn.DEFAULT_ANISOTROPY,_=fs){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:Ob++}),this.uuid=hl(),this.name="",this.source=new Dp(e),this.mipmaps=[],this.mapping=i,this.channel=0,this.wrapS=r,this.wrapT=l,this.magFilter=c,this.minFilter=f,this.anisotropy=d,this.format=p,this.internalFormat=null,this.type=m,this.offset=new mt(0,0),this.repeat=new mt(1,1),this.center=new mt(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new dt,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=_,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0}get width(){return this.source.getSize(jh).x}get height(){return this.source.getSize(jh).y}get depth(){return this.source.getSize(jh).z}get image(){return this.source.data}set image(e=null){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,i){this.updateRanges.push({start:e,count:i})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(const i in e){const r=e[i];if(r===void 0){st(`Texture.setValues(): parameter '${i}' has value of undefined.`);continue}const l=this[i];if(l===void 0){st(`Texture.setValues(): property '${i}' does not exist.`);continue}l&&r&&l.isVector2&&r.isVector2||l&&r&&l.isVector3&&r.isVector3||l&&r&&l.isMatrix3&&r.isMatrix3?l.copy(r):this[i]=r}}toJSON(e){const i=e===void 0||typeof e=="string";if(!i&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];const r={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(r.userData=this.userData),i||(e.textures[this.uuid]=r),r}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==rx)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Cd:e.x=e.x-Math.floor(e.x);break;case Ma:e.x=e.x<0?0:1;break;case wd:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Cd:e.y=e.y-Math.floor(e.y);break;case Ma:e.y=e.y<0?0:1;break;case wd:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}}Bn.DEFAULT_IMAGE=null;Bn.DEFAULT_MAPPING=rx;Bn.DEFAULT_ANISOTROPY=1;class rn{constructor(e=0,i=0,r=0,l=1){rn.prototype.isVector4=!0,this.x=e,this.y=i,this.z=r,this.w=l}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,i,r,l){return this.x=e,this.y=i,this.z=r,this.w=l,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,i){switch(e){case 0:this.x=i;break;case 1:this.y=i;break;case 2:this.z=i;break;case 3:this.w=i;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,i){return this.x=e.x+i.x,this.y=e.y+i.y,this.z=e.z+i.z,this.w=e.w+i.w,this}addScaledVector(e,i){return this.x+=e.x*i,this.y+=e.y*i,this.z+=e.z*i,this.w+=e.w*i,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,i){return this.x=e.x-i.x,this.y=e.y-i.y,this.z=e.z-i.z,this.w=e.w-i.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){const i=this.x,r=this.y,l=this.z,c=this.w,f=e.elements;return this.x=f[0]*i+f[4]*r+f[8]*l+f[12]*c,this.y=f[1]*i+f[5]*r+f[9]*l+f[13]*c,this.z=f[2]*i+f[6]*r+f[10]*l+f[14]*c,this.w=f[3]*i+f[7]*r+f[11]*l+f[15]*c,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);const i=Math.sqrt(1-e.w*e.w);return i<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/i,this.y=e.y/i,this.z=e.z/i),this}setAxisAngleFromRotationMatrix(e){let i,r,l,c;const m=e.elements,d=m[0],_=m[4],v=m[8],g=m[1],M=m[5],E=m[9],R=m[2],x=m[6],y=m[10];if(Math.abs(_-g)<.01&&Math.abs(v-R)<.01&&Math.abs(E-x)<.01){if(Math.abs(_+g)<.1&&Math.abs(v+R)<.1&&Math.abs(E+x)<.1&&Math.abs(d+M+y-3)<.1)return this.set(1,0,0,0),this;i=Math.PI;const U=(d+1)/2,P=(M+1)/2,V=(y+1)/2,H=(_+g)/4,z=(v+R)/4,A=(E+x)/4;return U>P&&U>V?U<.01?(r=0,l=.707106781,c=.707106781):(r=Math.sqrt(U),l=H/r,c=z/r):P>V?P<.01?(r=.707106781,l=0,c=.707106781):(l=Math.sqrt(P),r=H/l,c=A/l):V<.01?(r=.707106781,l=.707106781,c=0):(c=Math.sqrt(V),r=z/c,l=A/c),this.set(r,l,c,i),this}let T=Math.sqrt((x-E)*(x-E)+(v-R)*(v-R)+(g-_)*(g-_));return Math.abs(T)<.001&&(T=1),this.x=(x-E)/T,this.y=(v-R)/T,this.z=(g-_)/T,this.w=Math.acos((d+M+y-1)/2),this}setFromMatrixPosition(e){const i=e.elements;return this.x=i[12],this.y=i[13],this.z=i[14],this.w=i[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,i){return this.x=xt(this.x,e.x,i.x),this.y=xt(this.y,e.y,i.y),this.z=xt(this.z,e.z,i.z),this.w=xt(this.w,e.w,i.w),this}clampScalar(e,i){return this.x=xt(this.x,e,i),this.y=xt(this.y,e,i),this.z=xt(this.z,e,i),this.w=xt(this.w,e,i),this}clampLength(e,i){const r=this.length();return this.divideScalar(r||1).multiplyScalar(xt(r,e,i))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,i){return this.x+=(e.x-this.x)*i,this.y+=(e.y-this.y)*i,this.z+=(e.z-this.z)*i,this.w+=(e.w-this.w)*i,this}lerpVectors(e,i,r){return this.x=e.x+(i.x-e.x)*r,this.y=e.y+(i.y-e.y)*r,this.z=e.z+(i.z-e.z)*r,this.w=e.w+(i.w-e.w)*r,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,i=0){return this.x=e[i],this.y=e[i+1],this.z=e[i+2],this.w=e[i+3],this}toArray(e=[],i=0){return e[i]=this.x,e[i+1]=this.y,e[i+2]=this.z,e[i+3]=this.w,e}fromBufferAttribute(e,i){return this.x=e.getX(i),this.y=e.getY(i),this.z=e.getZ(i),this.w=e.getW(i),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}}class Pb extends Xs{constructor(e=1,i=1,r={}){super(),r=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:Nn,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1},r),this.isRenderTarget=!0,this.width=e,this.height=i,this.depth=r.depth,this.scissor=new rn(0,0,e,i),this.scissorTest=!1,this.viewport=new rn(0,0,e,i),this.textures=[];const l={width:e,height:i,depth:r.depth},c=new Bn(l),f=r.count;for(let p=0;p<f;p++)this.textures[p]=c.clone(),this.textures[p].isRenderTargetTexture=!0,this.textures[p].renderTarget=this;this._setTextureOptions(r),this.depthBuffer=r.depthBuffer,this.stencilBuffer=r.stencilBuffer,this.resolveDepthBuffer=r.resolveDepthBuffer,this.resolveStencilBuffer=r.resolveStencilBuffer,this._depthTexture=null,this.depthTexture=r.depthTexture,this.samples=r.samples,this.multiview=r.multiview}_setTextureOptions(e={}){const i={minFilter:Nn,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(i.mapping=e.mapping),e.wrapS!==void 0&&(i.wrapS=e.wrapS),e.wrapT!==void 0&&(i.wrapT=e.wrapT),e.wrapR!==void 0&&(i.wrapR=e.wrapR),e.magFilter!==void 0&&(i.magFilter=e.magFilter),e.minFilter!==void 0&&(i.minFilter=e.minFilter),e.format!==void 0&&(i.format=e.format),e.type!==void 0&&(i.type=e.type),e.anisotropy!==void 0&&(i.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(i.colorSpace=e.colorSpace),e.flipY!==void 0&&(i.flipY=e.flipY),e.generateMipmaps!==void 0&&(i.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(i.internalFormat=e.internalFormat);for(let r=0;r<this.textures.length;r++)this.textures[r].setValues(i)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&(this._depthTexture.renderTarget=null),e!==null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,i,r=1){if(this.width!==e||this.height!==i||this.depth!==r){this.width=e,this.height=i,this.depth=r;for(let l=0,c=this.textures.length;l<c;l++)this.textures[l].image.width=e,this.textures[l].image.height=i,this.textures[l].image.depth=r,this.textures[l].isData3DTexture!==!0&&(this.textures[l].isArrayTexture=this.textures[l].image.depth>1);this.dispose()}this.viewport.set(0,0,e,i),this.scissor.set(0,0,e,i)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let i=0,r=e.textures.length;i<r;i++){this.textures[i]=e.textures[i].clone(),this.textures[i].isRenderTargetTexture=!0,this.textures[i].renderTarget=this;const l=Object.assign({},e.textures[i].image);this.textures[i].source=new Dp(l)}return this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,e.depthTexture!==null&&(this.depthTexture=e.depthTexture.clone()),this.samples=e.samples,this}dispose(){this.dispatchEvent({type:"dispose"})}}class Yi extends Pb{constructor(e=1,i=1,r={}){super(e,i,r),this.isWebGLRenderTarget=!0}}class mx extends Bn{constructor(e=null,i=1,r=1,l=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:i,height:r,depth:l},this.magFilter=Rn,this.minFilter=Rn,this.wrapR=Ma,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}}class Fb extends Bn{constructor(e=null,i=1,r=1,l=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:i,height:r,depth:l},this.magFilter=Rn,this.minFilter=Rn,this.wrapR=Ma,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}class nn{constructor(e,i,r,l,c,f,p,m,d,_,v,g,M,E,R,x){nn.prototype.isMatrix4=!0,this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,i,r,l,c,f,p,m,d,_,v,g,M,E,R,x)}set(e,i,r,l,c,f,p,m,d,_,v,g,M,E,R,x){const y=this.elements;return y[0]=e,y[4]=i,y[8]=r,y[12]=l,y[1]=c,y[5]=f,y[9]=p,y[13]=m,y[2]=d,y[6]=_,y[10]=v,y[14]=g,y[3]=M,y[7]=E,y[11]=R,y[15]=x,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new nn().fromArray(this.elements)}copy(e){const i=this.elements,r=e.elements;return i[0]=r[0],i[1]=r[1],i[2]=r[2],i[3]=r[3],i[4]=r[4],i[5]=r[5],i[6]=r[6],i[7]=r[7],i[8]=r[8],i[9]=r[9],i[10]=r[10],i[11]=r[11],i[12]=r[12],i[13]=r[13],i[14]=r[14],i[15]=r[15],this}copyPosition(e){const i=this.elements,r=e.elements;return i[12]=r[12],i[13]=r[13],i[14]=r[14],this}setFromMatrix3(e){const i=e.elements;return this.set(i[0],i[3],i[6],0,i[1],i[4],i[7],0,i[2],i[5],i[8],0,0,0,0,1),this}extractBasis(e,i,r){return this.determinant()===0?(e.set(1,0,0),i.set(0,1,0),r.set(0,0,1),this):(e.setFromMatrixColumn(this,0),i.setFromMatrixColumn(this,1),r.setFromMatrixColumn(this,2),this)}makeBasis(e,i,r){return this.set(e.x,i.x,r.x,0,e.y,i.y,r.y,0,e.z,i.z,r.z,0,0,0,0,1),this}extractRotation(e){if(e.determinant()===0)return this.identity();const i=this.elements,r=e.elements,l=1/Dr.setFromMatrixColumn(e,0).length(),c=1/Dr.setFromMatrixColumn(e,1).length(),f=1/Dr.setFromMatrixColumn(e,2).length();return i[0]=r[0]*l,i[1]=r[1]*l,i[2]=r[2]*l,i[3]=0,i[4]=r[4]*c,i[5]=r[5]*c,i[6]=r[6]*c,i[7]=0,i[8]=r[8]*f,i[9]=r[9]*f,i[10]=r[10]*f,i[11]=0,i[12]=0,i[13]=0,i[14]=0,i[15]=1,this}makeRotationFromEuler(e){const i=this.elements,r=e.x,l=e.y,c=e.z,f=Math.cos(r),p=Math.sin(r),m=Math.cos(l),d=Math.sin(l),_=Math.cos(c),v=Math.sin(c);if(e.order==="XYZ"){const g=f*_,M=f*v,E=p*_,R=p*v;i[0]=m*_,i[4]=-m*v,i[8]=d,i[1]=M+E*d,i[5]=g-R*d,i[9]=-p*m,i[2]=R-g*d,i[6]=E+M*d,i[10]=f*m}else if(e.order==="YXZ"){const g=m*_,M=m*v,E=d*_,R=d*v;i[0]=g+R*p,i[4]=E*p-M,i[8]=f*d,i[1]=f*v,i[5]=f*_,i[9]=-p,i[2]=M*p-E,i[6]=R+g*p,i[10]=f*m}else if(e.order==="ZXY"){const g=m*_,M=m*v,E=d*_,R=d*v;i[0]=g-R*p,i[4]=-f*v,i[8]=E+M*p,i[1]=M+E*p,i[5]=f*_,i[9]=R-g*p,i[2]=-f*d,i[6]=p,i[10]=f*m}else if(e.order==="ZYX"){const g=f*_,M=f*v,E=p*_,R=p*v;i[0]=m*_,i[4]=E*d-M,i[8]=g*d+R,i[1]=m*v,i[5]=R*d+g,i[9]=M*d-E,i[2]=-d,i[6]=p*m,i[10]=f*m}else if(e.order==="YZX"){const g=f*m,M=f*d,E=p*m,R=p*d;i[0]=m*_,i[4]=R-g*v,i[8]=E*v+M,i[1]=v,i[5]=f*_,i[9]=-p*_,i[2]=-d*_,i[6]=M*v+E,i[10]=g-R*v}else if(e.order==="XZY"){const g=f*m,M=f*d,E=p*m,R=p*d;i[0]=m*_,i[4]=-v,i[8]=d*_,i[1]=g*v+R,i[5]=f*_,i[9]=M*v-E,i[2]=E*v-M,i[6]=p*_,i[10]=R*v+g}return i[3]=0,i[7]=0,i[11]=0,i[12]=0,i[13]=0,i[14]=0,i[15]=1,this}makeRotationFromQuaternion(e){return this.compose(Ib,e,zb)}lookAt(e,i,r){const l=this.elements;return ri.subVectors(e,i),ri.lengthSq()===0&&(ri.z=1),ri.normalize(),as.crossVectors(r,ri),as.lengthSq()===0&&(Math.abs(r.z)===1?ri.x+=1e-4:ri.z+=1e-4,ri.normalize(),as.crossVectors(r,ri)),as.normalize(),Nc.crossVectors(ri,as),l[0]=as.x,l[4]=Nc.x,l[8]=ri.x,l[1]=as.y,l[5]=Nc.y,l[9]=ri.y,l[2]=as.z,l[6]=Nc.z,l[10]=ri.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,i){const r=e.elements,l=i.elements,c=this.elements,f=r[0],p=r[4],m=r[8],d=r[12],_=r[1],v=r[5],g=r[9],M=r[13],E=r[2],R=r[6],x=r[10],y=r[14],T=r[3],U=r[7],P=r[11],V=r[15],H=l[0],z=l[4],A=l[8],L=l[12],pe=l[1],w=l[5],Y=l[9],re=l[13],fe=l[2],ee=l[6],I=l[10],B=l[14],$=l[3],Q=l[7],de=l[11],O=l[15];return c[0]=f*H+p*pe+m*fe+d*$,c[4]=f*z+p*w+m*ee+d*Q,c[8]=f*A+p*Y+m*I+d*de,c[12]=f*L+p*re+m*B+d*O,c[1]=_*H+v*pe+g*fe+M*$,c[5]=_*z+v*w+g*ee+M*Q,c[9]=_*A+v*Y+g*I+M*de,c[13]=_*L+v*re+g*B+M*O,c[2]=E*H+R*pe+x*fe+y*$,c[6]=E*z+R*w+x*ee+y*Q,c[10]=E*A+R*Y+x*I+y*de,c[14]=E*L+R*re+x*B+y*O,c[3]=T*H+U*pe+P*fe+V*$,c[7]=T*z+U*w+P*ee+V*Q,c[11]=T*A+U*Y+P*I+V*de,c[15]=T*L+U*re+P*B+V*O,this}multiplyScalar(e){const i=this.elements;return i[0]*=e,i[4]*=e,i[8]*=e,i[12]*=e,i[1]*=e,i[5]*=e,i[9]*=e,i[13]*=e,i[2]*=e,i[6]*=e,i[10]*=e,i[14]*=e,i[3]*=e,i[7]*=e,i[11]*=e,i[15]*=e,this}determinant(){const e=this.elements,i=e[0],r=e[4],l=e[8],c=e[12],f=e[1],p=e[5],m=e[9],d=e[13],_=e[2],v=e[6],g=e[10],M=e[14],E=e[3],R=e[7],x=e[11],y=e[15],T=m*M-d*g,U=p*M-d*v,P=p*g-m*v,V=f*M-d*_,H=f*g-m*_,z=f*v-p*_;return i*(R*T-x*U+y*P)-r*(E*T-x*V+y*H)+l*(E*U-R*V+y*z)-c*(E*P-R*H+x*z)}transpose(){const e=this.elements;let i;return i=e[1],e[1]=e[4],e[4]=i,i=e[2],e[2]=e[8],e[8]=i,i=e[6],e[6]=e[9],e[9]=i,i=e[3],e[3]=e[12],e[12]=i,i=e[7],e[7]=e[13],e[13]=i,i=e[11],e[11]=e[14],e[14]=i,this}setPosition(e,i,r){const l=this.elements;return e.isVector3?(l[12]=e.x,l[13]=e.y,l[14]=e.z):(l[12]=e,l[13]=i,l[14]=r),this}invert(){const e=this.elements,i=e[0],r=e[1],l=e[2],c=e[3],f=e[4],p=e[5],m=e[6],d=e[7],_=e[8],v=e[9],g=e[10],M=e[11],E=e[12],R=e[13],x=e[14],y=e[15],T=i*p-r*f,U=i*m-l*f,P=i*d-c*f,V=r*m-l*p,H=r*d-c*p,z=l*d-c*m,A=_*R-v*E,L=_*x-g*E,pe=_*y-M*E,w=v*x-g*R,Y=v*y-M*R,re=g*y-M*x,fe=T*re-U*Y+P*w+V*pe-H*L+z*A;if(fe===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);const ee=1/fe;return e[0]=(p*re-m*Y+d*w)*ee,e[1]=(l*Y-r*re-c*w)*ee,e[2]=(R*z-x*H+y*V)*ee,e[3]=(g*H-v*z-M*V)*ee,e[4]=(m*pe-f*re-d*L)*ee,e[5]=(i*re-l*pe+c*L)*ee,e[6]=(x*P-E*z-y*U)*ee,e[7]=(_*z-g*P+M*U)*ee,e[8]=(f*Y-p*pe+d*A)*ee,e[9]=(r*pe-i*Y-c*A)*ee,e[10]=(E*H-R*P+y*T)*ee,e[11]=(v*P-_*H-M*T)*ee,e[12]=(p*L-f*w-m*A)*ee,e[13]=(i*w-r*L+l*A)*ee,e[14]=(R*U-E*V-x*T)*ee,e[15]=(_*V-v*U+g*T)*ee,this}scale(e){const i=this.elements,r=e.x,l=e.y,c=e.z;return i[0]*=r,i[4]*=l,i[8]*=c,i[1]*=r,i[5]*=l,i[9]*=c,i[2]*=r,i[6]*=l,i[10]*=c,i[3]*=r,i[7]*=l,i[11]*=c,this}getMaxScaleOnAxis(){const e=this.elements,i=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],r=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],l=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(i,r,l))}makeTranslation(e,i,r){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,i,0,0,1,r,0,0,0,1),this}makeRotationX(e){const i=Math.cos(e),r=Math.sin(e);return this.set(1,0,0,0,0,i,-r,0,0,r,i,0,0,0,0,1),this}makeRotationY(e){const i=Math.cos(e),r=Math.sin(e);return this.set(i,0,r,0,0,1,0,0,-r,0,i,0,0,0,0,1),this}makeRotationZ(e){const i=Math.cos(e),r=Math.sin(e);return this.set(i,-r,0,0,r,i,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,i){const r=Math.cos(i),l=Math.sin(i),c=1-r,f=e.x,p=e.y,m=e.z,d=c*f,_=c*p;return this.set(d*f+r,d*p-l*m,d*m+l*p,0,d*p+l*m,_*p+r,_*m-l*f,0,d*m-l*p,_*m+l*f,c*m*m+r,0,0,0,0,1),this}makeScale(e,i,r){return this.set(e,0,0,0,0,i,0,0,0,0,r,0,0,0,0,1),this}makeShear(e,i,r,l,c,f){return this.set(1,r,c,0,e,1,f,0,i,l,1,0,0,0,0,1),this}compose(e,i,r){const l=this.elements,c=i._x,f=i._y,p=i._z,m=i._w,d=c+c,_=f+f,v=p+p,g=c*d,M=c*_,E=c*v,R=f*_,x=f*v,y=p*v,T=m*d,U=m*_,P=m*v,V=r.x,H=r.y,z=r.z;return l[0]=(1-(R+y))*V,l[1]=(M+P)*V,l[2]=(E-U)*V,l[3]=0,l[4]=(M-P)*H,l[5]=(1-(g+y))*H,l[6]=(x+T)*H,l[7]=0,l[8]=(E+U)*z,l[9]=(x-T)*z,l[10]=(1-(g+R))*z,l[11]=0,l[12]=e.x,l[13]=e.y,l[14]=e.z,l[15]=1,this}decompose(e,i,r){const l=this.elements;e.x=l[12],e.y=l[13],e.z=l[14];const c=this.determinant();if(c===0)return r.set(1,1,1),i.identity(),this;let f=Dr.set(l[0],l[1],l[2]).length();const p=Dr.set(l[4],l[5],l[6]).length(),m=Dr.set(l[8],l[9],l[10]).length();c<0&&(f=-f),wi.copy(this);const d=1/f,_=1/p,v=1/m;return wi.elements[0]*=d,wi.elements[1]*=d,wi.elements[2]*=d,wi.elements[4]*=_,wi.elements[5]*=_,wi.elements[6]*=_,wi.elements[8]*=v,wi.elements[9]*=v,wi.elements[10]*=v,i.setFromRotationMatrix(wi),r.x=f,r.y=p,r.z=m,this}makePerspective(e,i,r,l,c,f,p=Wi,m=!1){const d=this.elements,_=2*c/(i-e),v=2*c/(r-l),g=(i+e)/(i-e),M=(r+l)/(r-l);let E,R;if(m)E=c/(f-c),R=f*c/(f-c);else if(p===Wi)E=-(f+c)/(f-c),R=-2*f*c/(f-c);else if(p===du)E=-f/(f-c),R=-f*c/(f-c);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+p);return d[0]=_,d[4]=0,d[8]=g,d[12]=0,d[1]=0,d[5]=v,d[9]=M,d[13]=0,d[2]=0,d[6]=0,d[10]=E,d[14]=R,d[3]=0,d[7]=0,d[11]=-1,d[15]=0,this}makeOrthographic(e,i,r,l,c,f,p=Wi,m=!1){const d=this.elements,_=2/(i-e),v=2/(r-l),g=-(i+e)/(i-e),M=-(r+l)/(r-l);let E,R;if(m)E=1/(f-c),R=f/(f-c);else if(p===Wi)E=-2/(f-c),R=-(f+c)/(f-c);else if(p===du)E=-1/(f-c),R=-c/(f-c);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+p);return d[0]=_,d[4]=0,d[8]=0,d[12]=g,d[1]=0,d[5]=v,d[9]=0,d[13]=M,d[2]=0,d[6]=0,d[10]=E,d[14]=R,d[3]=0,d[7]=0,d[11]=0,d[15]=1,this}equals(e){const i=this.elements,r=e.elements;for(let l=0;l<16;l++)if(i[l]!==r[l])return!1;return!0}fromArray(e,i=0){for(let r=0;r<16;r++)this.elements[r]=e[r+i];return this}toArray(e=[],i=0){const r=this.elements;return e[i]=r[0],e[i+1]=r[1],e[i+2]=r[2],e[i+3]=r[3],e[i+4]=r[4],e[i+5]=r[5],e[i+6]=r[6],e[i+7]=r[7],e[i+8]=r[8],e[i+9]=r[9],e[i+10]=r[10],e[i+11]=r[11],e[i+12]=r[12],e[i+13]=r[13],e[i+14]=r[14],e[i+15]=r[15],e}}const Dr=new se,wi=new nn,Ib=new se(0,0,0),zb=new se(1,1,1),as=new se,Nc=new se,ri=new se,G0=new nn,V0=new ps;class Da{constructor(e=0,i=0,r=0,l=Da.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=i,this._z=r,this._order=l}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,i,r,l=this._order){return this._x=e,this._y=i,this._z=r,this._order=l,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,i=this._order,r=!0){const l=e.elements,c=l[0],f=l[4],p=l[8],m=l[1],d=l[5],_=l[9],v=l[2],g=l[6],M=l[10];switch(i){case"XYZ":this._y=Math.asin(xt(p,-1,1)),Math.abs(p)<.9999999?(this._x=Math.atan2(-_,M),this._z=Math.atan2(-f,c)):(this._x=Math.atan2(g,d),this._z=0);break;case"YXZ":this._x=Math.asin(-xt(_,-1,1)),Math.abs(_)<.9999999?(this._y=Math.atan2(p,M),this._z=Math.atan2(m,d)):(this._y=Math.atan2(-v,c),this._z=0);break;case"ZXY":this._x=Math.asin(xt(g,-1,1)),Math.abs(g)<.9999999?(this._y=Math.atan2(-v,M),this._z=Math.atan2(-f,d)):(this._y=0,this._z=Math.atan2(m,c));break;case"ZYX":this._y=Math.asin(-xt(v,-1,1)),Math.abs(v)<.9999999?(this._x=Math.atan2(g,M),this._z=Math.atan2(m,c)):(this._x=0,this._z=Math.atan2(-f,d));break;case"YZX":this._z=Math.asin(xt(m,-1,1)),Math.abs(m)<.9999999?(this._x=Math.atan2(-_,d),this._y=Math.atan2(-v,c)):(this._x=0,this._y=Math.atan2(p,M));break;case"XZY":this._z=Math.asin(-xt(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(g,d),this._y=Math.atan2(p,c)):(this._x=Math.atan2(-_,M),this._y=0);break;default:st("Euler: .setFromRotationMatrix() encountered an unknown order: "+i)}return this._order=i,r===!0&&this._onChangeCallback(),this}setFromQuaternion(e,i,r){return G0.makeRotationFromQuaternion(e),this.setFromRotationMatrix(G0,i,r)}setFromVector3(e,i=this._order){return this.set(e.x,e.y,e.z,i)}reorder(e){return V0.setFromEuler(this),this.setFromQuaternion(V0,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],i=0){return e[i]=this._x,e[i+1]=this._y,e[i+2]=this._z,e[i+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}Da.DEFAULT_ORDER="XYZ";class Np{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}}let Bb=0;const k0=new se,Nr=new ps,ga=new nn,Uc=new se,Zo=new se,Hb=new se,Gb=new ps,j0=new se(1,0,0),X0=new se(0,1,0),W0=new se(0,0,1),q0={type:"added"},Vb={type:"removed"},Ur={type:"childadded",child:null},Xh={type:"childremoved",child:null};class Kn extends Xs{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Bb++}),this.uuid=hl(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=Kn.DEFAULT_UP.clone();const e=new se,i=new Da,r=new ps,l=new se(1,1,1);function c(){r.setFromEuler(i,!1)}function f(){i.setFromQuaternion(r,void 0,!1)}i._onChange(c),r._onChange(f),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:i},quaternion:{configurable:!0,enumerable:!0,value:r},scale:{configurable:!0,enumerable:!0,value:l},modelViewMatrix:{value:new nn},normalMatrix:{value:new dt}}),this.matrix=new nn,this.matrixWorld=new nn,this.matrixAutoUpdate=Kn.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=Kn.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Np,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,i){this.quaternion.setFromAxisAngle(e,i)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,i){return Nr.setFromAxisAngle(e,i),this.quaternion.multiply(Nr),this}rotateOnWorldAxis(e,i){return Nr.setFromAxisAngle(e,i),this.quaternion.premultiply(Nr),this}rotateX(e){return this.rotateOnAxis(j0,e)}rotateY(e){return this.rotateOnAxis(X0,e)}rotateZ(e){return this.rotateOnAxis(W0,e)}translateOnAxis(e,i){return k0.copy(e).applyQuaternion(this.quaternion),this.position.add(k0.multiplyScalar(i)),this}translateX(e){return this.translateOnAxis(j0,e)}translateY(e){return this.translateOnAxis(X0,e)}translateZ(e){return this.translateOnAxis(W0,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(ga.copy(this.matrixWorld).invert())}lookAt(e,i,r){e.isVector3?Uc.copy(e):Uc.set(e,i,r);const l=this.parent;this.updateWorldMatrix(!0,!1),Zo.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?ga.lookAt(Zo,Uc,this.up):ga.lookAt(Uc,Zo,this.up),this.quaternion.setFromRotationMatrix(ga),l&&(ga.extractRotation(l.matrixWorld),Nr.setFromRotationMatrix(ga),this.quaternion.premultiply(Nr.invert()))}add(e){if(arguments.length>1){for(let i=0;i<arguments.length;i++)this.add(arguments[i]);return this}return e===this?(At("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(q0),Ur.child=e,this.dispatchEvent(Ur),Ur.child=null):At("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let r=0;r<arguments.length;r++)this.remove(arguments[r]);return this}const i=this.children.indexOf(e);return i!==-1&&(e.parent=null,this.children.splice(i,1),e.dispatchEvent(Vb),Xh.child=e,this.dispatchEvent(Xh),Xh.child=null),this}removeFromParent(){const e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),ga.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),ga.multiply(e.parent.matrixWorld)),e.applyMatrix4(ga),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(q0),Ur.child=e,this.dispatchEvent(Ur),Ur.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,i){if(this[e]===i)return this;for(let r=0,l=this.children.length;r<l;r++){const f=this.children[r].getObjectByProperty(e,i);if(f!==void 0)return f}}getObjectsByProperty(e,i,r=[]){this[e]===i&&r.push(this);const l=this.children;for(let c=0,f=l.length;c<f;c++)l[c].getObjectsByProperty(e,i,r);return r}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Zo,e,Hb),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Zo,Gb,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);const i=this.matrixWorld.elements;return e.set(i[8],i[9],i[10]).normalize()}raycast(){}traverse(e){e(this);const i=this.children;for(let r=0,l=i.length;r<l;r++)i[r].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);const i=this.children;for(let r=0,l=i.length;r<l;r++)i[r].traverseVisible(e)}traverseAncestors(e){const i=this.parent;i!==null&&(e(i),i.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);const e=this.pivot;if(e!==null){const i=e.x,r=e.y,l=e.z,c=this.matrix.elements;c[12]+=i-c[0]*i-c[4]*r-c[8]*l,c[13]+=r-c[1]*i-c[5]*r-c[9]*l,c[14]+=l-c[2]*i-c[6]*r-c[10]*l}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);const i=this.children;for(let r=0,l=i.length;r<l;r++)i[r].updateMatrixWorld(e)}updateWorldMatrix(e,i){const r=this.parent;if(e===!0&&r!==null&&r.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),i===!0){const l=this.children;for(let c=0,f=l.length;c<f;c++)l[c].updateWorldMatrix(!1,!0)}}toJSON(e){const i=e===void 0||typeof e=="string",r={};i&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},r.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});const l={};l.uuid=this.uuid,l.type=this.type,this.name!==""&&(l.name=this.name),this.castShadow===!0&&(l.castShadow=!0),this.receiveShadow===!0&&(l.receiveShadow=!0),this.visible===!1&&(l.visible=!1),this.frustumCulled===!1&&(l.frustumCulled=!1),this.renderOrder!==0&&(l.renderOrder=this.renderOrder),this.static!==!1&&(l.static=this.static),Object.keys(this.userData).length>0&&(l.userData=this.userData),l.layers=this.layers.mask,l.matrix=this.matrix.toArray(),l.up=this.up.toArray(),this.pivot!==null&&(l.pivot=this.pivot.toArray()),this.matrixAutoUpdate===!1&&(l.matrixAutoUpdate=!1),this.morphTargetDictionary!==void 0&&(l.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(l.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(l.type="InstancedMesh",l.count=this.count,l.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(l.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(l.type="BatchedMesh",l.perObjectFrustumCulled=this.perObjectFrustumCulled,l.sortObjects=this.sortObjects,l.drawRanges=this._drawRanges,l.reservedRanges=this._reservedRanges,l.geometryInfo=this._geometryInfo.map(p=>({...p,boundingBox:p.boundingBox?p.boundingBox.toJSON():void 0,boundingSphere:p.boundingSphere?p.boundingSphere.toJSON():void 0})),l.instanceInfo=this._instanceInfo.map(p=>({...p})),l.availableInstanceIds=this._availableInstanceIds.slice(),l.availableGeometryIds=this._availableGeometryIds.slice(),l.nextIndexStart=this._nextIndexStart,l.nextVertexStart=this._nextVertexStart,l.geometryCount=this._geometryCount,l.maxInstanceCount=this._maxInstanceCount,l.maxVertexCount=this._maxVertexCount,l.maxIndexCount=this._maxIndexCount,l.geometryInitialized=this._geometryInitialized,l.matricesTexture=this._matricesTexture.toJSON(e),l.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(l.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(l.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(l.boundingBox=this.boundingBox.toJSON()));function c(p,m){return p[m.uuid]===void 0&&(p[m.uuid]=m.toJSON(e)),m.uuid}if(this.isScene)this.background&&(this.background.isColor?l.background=this.background.toJSON():this.background.isTexture&&(l.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(l.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){l.geometry=c(e.geometries,this.geometry);const p=this.geometry.parameters;if(p!==void 0&&p.shapes!==void 0){const m=p.shapes;if(Array.isArray(m))for(let d=0,_=m.length;d<_;d++){const v=m[d];c(e.shapes,v)}else c(e.shapes,m)}}if(this.isSkinnedMesh&&(l.bindMode=this.bindMode,l.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(c(e.skeletons,this.skeleton),l.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){const p=[];for(let m=0,d=this.material.length;m<d;m++)p.push(c(e.materials,this.material[m]));l.material=p}else l.material=c(e.materials,this.material);if(this.children.length>0){l.children=[];for(let p=0;p<this.children.length;p++)l.children.push(this.children[p].toJSON(e).object)}if(this.animations.length>0){l.animations=[];for(let p=0;p<this.animations.length;p++){const m=this.animations[p];l.animations.push(c(e.animations,m))}}if(i){const p=f(e.geometries),m=f(e.materials),d=f(e.textures),_=f(e.images),v=f(e.shapes),g=f(e.skeletons),M=f(e.animations),E=f(e.nodes);p.length>0&&(r.geometries=p),m.length>0&&(r.materials=m),d.length>0&&(r.textures=d),_.length>0&&(r.images=_),v.length>0&&(r.shapes=v),g.length>0&&(r.skeletons=g),M.length>0&&(r.animations=M),E.length>0&&(r.nodes=E)}return r.object=l,r;function f(p){const m=[];for(const d in p){const _=p[d];delete _.metadata,m.push(_)}return m}}clone(e){return new this.constructor().copy(this,e)}copy(e,i=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),e.pivot!==null&&(this.pivot=e.pivot.clone()),this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),i===!0)for(let r=0;r<e.children.length;r++){const l=e.children[r];this.add(l.clone())}return this}}Kn.DEFAULT_UP=new se(0,1,0);Kn.DEFAULT_MATRIX_AUTO_UPDATE=!0;Kn.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;class Lc extends Kn{constructor(){super(),this.isGroup=!0,this.type="Group"}}const kb={type:"move"};class Wh{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new Lc,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new Lc,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new se,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new se),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new Lc,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new se,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new se),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){const i=this._hand;if(i)for(const r of e.hand.values())this._getHandJoint(i,r)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,i,r){let l=null,c=null,f=null;const p=this._targetRay,m=this._grip,d=this._hand;if(e&&i.session.visibilityState!=="visible-blurred"){if(d&&e.hand){f=!0;for(const R of e.hand.values()){const x=i.getJointPose(R,r),y=this._getHandJoint(d,R);x!==null&&(y.matrix.fromArray(x.transform.matrix),y.matrix.decompose(y.position,y.rotation,y.scale),y.matrixWorldNeedsUpdate=!0,y.jointRadius=x.radius),y.visible=x!==null}const _=d.joints["index-finger-tip"],v=d.joints["thumb-tip"],g=_.position.distanceTo(v.position),M=.02,E=.005;d.inputState.pinching&&g>M+E?(d.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!d.inputState.pinching&&g<=M-E&&(d.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else m!==null&&e.gripSpace&&(c=i.getPose(e.gripSpace,r),c!==null&&(m.matrix.fromArray(c.transform.matrix),m.matrix.decompose(m.position,m.rotation,m.scale),m.matrixWorldNeedsUpdate=!0,c.linearVelocity?(m.hasLinearVelocity=!0,m.linearVelocity.copy(c.linearVelocity)):m.hasLinearVelocity=!1,c.angularVelocity?(m.hasAngularVelocity=!0,m.angularVelocity.copy(c.angularVelocity)):m.hasAngularVelocity=!1));p!==null&&(l=i.getPose(e.targetRaySpace,r),l===null&&c!==null&&(l=c),l!==null&&(p.matrix.fromArray(l.transform.matrix),p.matrix.decompose(p.position,p.rotation,p.scale),p.matrixWorldNeedsUpdate=!0,l.linearVelocity?(p.hasLinearVelocity=!0,p.linearVelocity.copy(l.linearVelocity)):p.hasLinearVelocity=!1,l.angularVelocity?(p.hasAngularVelocity=!0,p.angularVelocity.copy(l.angularVelocity)):p.hasAngularVelocity=!1,this.dispatchEvent(kb)))}return p!==null&&(p.visible=l!==null),m!==null&&(m.visible=c!==null),d!==null&&(d.visible=f!==null),this}_getHandJoint(e,i){if(e.joints[i.jointName]===void 0){const r=new Lc;r.matrixAutoUpdate=!1,r.visible=!1,e.joints[i.jointName]=r,e.add(r)}return e.joints[i.jointName]}}const gx={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},ss={h:0,s:0,l:0},Oc={h:0,s:0,l:0};function qh(s,e,i){return i<0&&(i+=1),i>1&&(i-=1),i<1/6?s+(e-s)*6*i:i<1/2?e:i<2/3?s+(e-s)*6*(2/3-i):s}class Lt{constructor(e,i,r){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,i,r)}set(e,i,r){if(i===void 0&&r===void 0){const l=e;l&&l.isColor?this.copy(l):typeof l=="number"?this.setHex(l):typeof l=="string"&&this.setStyle(l)}else this.setRGB(e,i,r);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,i=xi){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,Rt.colorSpaceToWorking(this,i),this}setRGB(e,i,r,l=Rt.workingColorSpace){return this.r=e,this.g=i,this.b=r,Rt.colorSpaceToWorking(this,l),this}setHSL(e,i,r,l=Rt.workingColorSpace){if(e=wb(e,1),i=xt(i,0,1),r=xt(r,0,1),i===0)this.r=this.g=this.b=r;else{const c=r<=.5?r*(1+i):r+i-r*i,f=2*r-c;this.r=qh(f,c,e+1/3),this.g=qh(f,c,e),this.b=qh(f,c,e-1/3)}return Rt.colorSpaceToWorking(this,l),this}setStyle(e,i=xi){function r(c){c!==void 0&&parseFloat(c)<1&&st("Color: Alpha component of "+e+" will be ignored.")}let l;if(l=/^(\w+)\(([^\)]*)\)/.exec(e)){let c;const f=l[1],p=l[2];switch(f){case"rgb":case"rgba":if(c=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(p))return r(c[4]),this.setRGB(Math.min(255,parseInt(c[1],10))/255,Math.min(255,parseInt(c[2],10))/255,Math.min(255,parseInt(c[3],10))/255,i);if(c=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(p))return r(c[4]),this.setRGB(Math.min(100,parseInt(c[1],10))/100,Math.min(100,parseInt(c[2],10))/100,Math.min(100,parseInt(c[3],10))/100,i);break;case"hsl":case"hsla":if(c=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(p))return r(c[4]),this.setHSL(parseFloat(c[1])/360,parseFloat(c[2])/100,parseFloat(c[3])/100,i);break;default:st("Color: Unknown color model "+e)}}else if(l=/^\#([A-Fa-f\d]+)$/.exec(e)){const c=l[1],f=c.length;if(f===3)return this.setRGB(parseInt(c.charAt(0),16)/15,parseInt(c.charAt(1),16)/15,parseInt(c.charAt(2),16)/15,i);if(f===6)return this.setHex(parseInt(c,16),i);st("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,i);return this}setColorName(e,i=xi){const r=gx[e.toLowerCase()];return r!==void 0?this.setHex(r,i):st("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=Ta(e.r),this.g=Ta(e.g),this.b=Ta(e.b),this}copyLinearToSRGB(e){return this.r=Xr(e.r),this.g=Xr(e.g),this.b=Xr(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=xi){return Rt.workingToColorSpace(Dn.copy(this),e),Math.round(xt(Dn.r*255,0,255))*65536+Math.round(xt(Dn.g*255,0,255))*256+Math.round(xt(Dn.b*255,0,255))}getHexString(e=xi){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,i=Rt.workingColorSpace){Rt.workingToColorSpace(Dn.copy(this),i);const r=Dn.r,l=Dn.g,c=Dn.b,f=Math.max(r,l,c),p=Math.min(r,l,c);let m,d;const _=(p+f)/2;if(p===f)m=0,d=0;else{const v=f-p;switch(d=_<=.5?v/(f+p):v/(2-f-p),f){case r:m=(l-c)/v+(l<c?6:0);break;case l:m=(c-r)/v+2;break;case c:m=(r-l)/v+4;break}m/=6}return e.h=m,e.s=d,e.l=_,e}getRGB(e,i=Rt.workingColorSpace){return Rt.workingToColorSpace(Dn.copy(this),i),e.r=Dn.r,e.g=Dn.g,e.b=Dn.b,e}getStyle(e=xi){Rt.workingToColorSpace(Dn.copy(this),e);const i=Dn.r,r=Dn.g,l=Dn.b;return e!==xi?`color(${e} ${i.toFixed(3)} ${r.toFixed(3)} ${l.toFixed(3)})`:`rgb(${Math.round(i*255)},${Math.round(r*255)},${Math.round(l*255)})`}offsetHSL(e,i,r){return this.getHSL(ss),this.setHSL(ss.h+e,ss.s+i,ss.l+r)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,i){return this.r=e.r+i.r,this.g=e.g+i.g,this.b=e.b+i.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,i){return this.r+=(e.r-this.r)*i,this.g+=(e.g-this.g)*i,this.b+=(e.b-this.b)*i,this}lerpColors(e,i,r){return this.r=e.r+(i.r-e.r)*r,this.g=e.g+(i.g-e.g)*r,this.b=e.b+(i.b-e.b)*r,this}lerpHSL(e,i){this.getHSL(ss),e.getHSL(Oc);const r=Hh(ss.h,Oc.h,i),l=Hh(ss.s,Oc.s,i),c=Hh(ss.l,Oc.l,i);return this.setHSL(r,l,c),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){const i=this.r,r=this.g,l=this.b,c=e.elements;return this.r=c[0]*i+c[3]*r+c[6]*l,this.g=c[1]*i+c[4]*r+c[7]*l,this.b=c[2]*i+c[5]*r+c[8]*l,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,i=0){return this.r=e[i],this.g=e[i+1],this.b=e[i+2],this}toArray(e=[],i=0){return e[i]=this.r,e[i+1]=this.g,e[i+2]=this.b,e}fromBufferAttribute(e,i){return this.r=e.getX(i),this.g=e.getY(i),this.b=e.getZ(i),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}const Dn=new Lt;Lt.NAMES=gx;class Up{constructor(e,i=1,r=1e3){this.isFog=!0,this.name="",this.color=new Lt(e),this.near=i,this.far=r}clone(){return new Up(this.color,this.near,this.far)}toJSON(){return{type:"Fog",name:this.name,color:this.color.getHex(),near:this.near,far:this.far}}}class jb extends Kn{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new Da,this.environmentIntensity=1,this.environmentRotation=new Da,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,i){return super.copy(e,i),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){const i=super.toJSON(e);return this.fog!==null&&(i.object.fog=this.fog.toJSON()),this.backgroundBlurriness>0&&(i.object.backgroundBlurriness=this.backgroundBlurriness),this.backgroundIntensity!==1&&(i.object.backgroundIntensity=this.backgroundIntensity),i.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1&&(i.object.environmentIntensity=this.environmentIntensity),i.object.environmentRotation=this.environmentRotation.toArray(),i}}const Di=new se,_a=new se,Yh=new se,va=new se,Lr=new se,Or=new se,Y0=new se,Zh=new se,Kh=new se,Qh=new se,Jh=new rn,$h=new rn,ed=new rn;class Ui{constructor(e=new se,i=new se,r=new se){this.a=e,this.b=i,this.c=r}static getNormal(e,i,r,l){l.subVectors(r,i),Di.subVectors(e,i),l.cross(Di);const c=l.lengthSq();return c>0?l.multiplyScalar(1/Math.sqrt(c)):l.set(0,0,0)}static getBarycoord(e,i,r,l,c){Di.subVectors(l,i),_a.subVectors(r,i),Yh.subVectors(e,i);const f=Di.dot(Di),p=Di.dot(_a),m=Di.dot(Yh),d=_a.dot(_a),_=_a.dot(Yh),v=f*d-p*p;if(v===0)return c.set(0,0,0),null;const g=1/v,M=(d*m-p*_)*g,E=(f*_-p*m)*g;return c.set(1-M-E,E,M)}static containsPoint(e,i,r,l){return this.getBarycoord(e,i,r,l,va)===null?!1:va.x>=0&&va.y>=0&&va.x+va.y<=1}static getInterpolation(e,i,r,l,c,f,p,m){return this.getBarycoord(e,i,r,l,va)===null?(m.x=0,m.y=0,"z"in m&&(m.z=0),"w"in m&&(m.w=0),null):(m.setScalar(0),m.addScaledVector(c,va.x),m.addScaledVector(f,va.y),m.addScaledVector(p,va.z),m)}static getInterpolatedAttribute(e,i,r,l,c,f){return Jh.setScalar(0),$h.setScalar(0),ed.setScalar(0),Jh.fromBufferAttribute(e,i),$h.fromBufferAttribute(e,r),ed.fromBufferAttribute(e,l),f.setScalar(0),f.addScaledVector(Jh,c.x),f.addScaledVector($h,c.y),f.addScaledVector(ed,c.z),f}static isFrontFacing(e,i,r,l){return Di.subVectors(r,i),_a.subVectors(e,i),Di.cross(_a).dot(l)<0}set(e,i,r){return this.a.copy(e),this.b.copy(i),this.c.copy(r),this}setFromPointsAndIndices(e,i,r,l){return this.a.copy(e[i]),this.b.copy(e[r]),this.c.copy(e[l]),this}setFromAttributeAndIndices(e,i,r,l){return this.a.fromBufferAttribute(e,i),this.b.fromBufferAttribute(e,r),this.c.fromBufferAttribute(e,l),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return Di.subVectors(this.c,this.b),_a.subVectors(this.a,this.b),Di.cross(_a).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return Ui.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,i){return Ui.getBarycoord(e,this.a,this.b,this.c,i)}getInterpolation(e,i,r,l,c){return Ui.getInterpolation(e,this.a,this.b,this.c,i,r,l,c)}containsPoint(e){return Ui.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return Ui.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,i){const r=this.a,l=this.b,c=this.c;let f,p;Lr.subVectors(l,r),Or.subVectors(c,r),Zh.subVectors(e,r);const m=Lr.dot(Zh),d=Or.dot(Zh);if(m<=0&&d<=0)return i.copy(r);Kh.subVectors(e,l);const _=Lr.dot(Kh),v=Or.dot(Kh);if(_>=0&&v<=_)return i.copy(l);const g=m*v-_*d;if(g<=0&&m>=0&&_<=0)return f=m/(m-_),i.copy(r).addScaledVector(Lr,f);Qh.subVectors(e,c);const M=Lr.dot(Qh),E=Or.dot(Qh);if(E>=0&&M<=E)return i.copy(c);const R=M*d-m*E;if(R<=0&&d>=0&&E<=0)return p=d/(d-E),i.copy(r).addScaledVector(Or,p);const x=_*E-M*v;if(x<=0&&v-_>=0&&M-E>=0)return Y0.subVectors(c,l),p=(v-_)/(v-_+(M-E)),i.copy(l).addScaledVector(Y0,p);const y=1/(x+R+g);return f=R*y,p=g*y,i.copy(r).addScaledVector(Lr,f).addScaledVector(Or,p)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}}class dl{constructor(e=new se(1/0,1/0,1/0),i=new se(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=i}set(e,i){return this.min.copy(e),this.max.copy(i),this}setFromArray(e){this.makeEmpty();for(let i=0,r=e.length;i<r;i+=3)this.expandByPoint(Ni.fromArray(e,i));return this}setFromBufferAttribute(e){this.makeEmpty();for(let i=0,r=e.count;i<r;i++)this.expandByPoint(Ni.fromBufferAttribute(e,i));return this}setFromPoints(e){this.makeEmpty();for(let i=0,r=e.length;i<r;i++)this.expandByPoint(e[i]);return this}setFromCenterAndSize(e,i){const r=Ni.copy(i).multiplyScalar(.5);return this.min.copy(e).sub(r),this.max.copy(e).add(r),this}setFromObject(e,i=!1){return this.makeEmpty(),this.expandByObject(e,i)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,i=!1){e.updateWorldMatrix(!1,!1);const r=e.geometry;if(r!==void 0){const c=r.getAttribute("position");if(i===!0&&c!==void 0&&e.isInstancedMesh!==!0)for(let f=0,p=c.count;f<p;f++)e.isMesh===!0?e.getVertexPosition(f,Ni):Ni.fromBufferAttribute(c,f),Ni.applyMatrix4(e.matrixWorld),this.expandByPoint(Ni);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),Pc.copy(e.boundingBox)):(r.boundingBox===null&&r.computeBoundingBox(),Pc.copy(r.boundingBox)),Pc.applyMatrix4(e.matrixWorld),this.union(Pc)}const l=e.children;for(let c=0,f=l.length;c<f;c++)this.expandByObject(l[c],i);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,i){return i.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,Ni),Ni.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let i,r;return e.normal.x>0?(i=e.normal.x*this.min.x,r=e.normal.x*this.max.x):(i=e.normal.x*this.max.x,r=e.normal.x*this.min.x),e.normal.y>0?(i+=e.normal.y*this.min.y,r+=e.normal.y*this.max.y):(i+=e.normal.y*this.max.y,r+=e.normal.y*this.min.y),e.normal.z>0?(i+=e.normal.z*this.min.z,r+=e.normal.z*this.max.z):(i+=e.normal.z*this.max.z,r+=e.normal.z*this.min.z),i<=-e.constant&&r>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(Ko),Fc.subVectors(this.max,Ko),Pr.subVectors(e.a,Ko),Fr.subVectors(e.b,Ko),Ir.subVectors(e.c,Ko),rs.subVectors(Fr,Pr),os.subVectors(Ir,Fr),Os.subVectors(Pr,Ir);let i=[0,-rs.z,rs.y,0,-os.z,os.y,0,-Os.z,Os.y,rs.z,0,-rs.x,os.z,0,-os.x,Os.z,0,-Os.x,-rs.y,rs.x,0,-os.y,os.x,0,-Os.y,Os.x,0];return!td(i,Pr,Fr,Ir,Fc)||(i=[1,0,0,0,1,0,0,0,1],!td(i,Pr,Fr,Ir,Fc))?!1:(Ic.crossVectors(rs,os),i=[Ic.x,Ic.y,Ic.z],td(i,Pr,Fr,Ir,Fc))}clampPoint(e,i){return i.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,Ni).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(Ni).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(xa[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),xa[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),xa[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),xa[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),xa[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),xa[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),xa[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),xa[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(xa),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}}const xa=[new se,new se,new se,new se,new se,new se,new se,new se],Ni=new se,Pc=new dl,Pr=new se,Fr=new se,Ir=new se,rs=new se,os=new se,Os=new se,Ko=new se,Fc=new se,Ic=new se,Ps=new se;function td(s,e,i,r,l){for(let c=0,f=s.length-3;c<=f;c+=3){Ps.fromArray(s,c);const p=l.x*Math.abs(Ps.x)+l.y*Math.abs(Ps.y)+l.z*Math.abs(Ps.z),m=e.dot(Ps),d=i.dot(Ps),_=r.dot(Ps);if(Math.max(-Math.max(m,d,_),Math.min(m,d,_))>p)return!1}return!0}const pn=new se,zc=new mt;let Xb=0;class Yn{constructor(e,i,r=!1){if(Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:Xb++}),this.name="",this.array=e,this.itemSize=i,this.count=e!==void 0?e.length/i:0,this.normalized=r,this.usage=O0,this.updateRanges=[],this.gpuType=Xi,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,i){this.updateRanges.push({start:e,count:i})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,i,r){e*=this.itemSize,r*=i.itemSize;for(let l=0,c=this.itemSize;l<c;l++)this.array[e+l]=i.array[r+l];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let i=0,r=this.count;i<r;i++)zc.fromBufferAttribute(this,i),zc.applyMatrix3(e),this.setXY(i,zc.x,zc.y);else if(this.itemSize===3)for(let i=0,r=this.count;i<r;i++)pn.fromBufferAttribute(this,i),pn.applyMatrix3(e),this.setXYZ(i,pn.x,pn.y,pn.z);return this}applyMatrix4(e){for(let i=0,r=this.count;i<r;i++)pn.fromBufferAttribute(this,i),pn.applyMatrix4(e),this.setXYZ(i,pn.x,pn.y,pn.z);return this}applyNormalMatrix(e){for(let i=0,r=this.count;i<r;i++)pn.fromBufferAttribute(this,i),pn.applyNormalMatrix(e),this.setXYZ(i,pn.x,pn.y,pn.z);return this}transformDirection(e){for(let i=0,r=this.count;i<r;i++)pn.fromBufferAttribute(this,i),pn.transformDirection(e),this.setXYZ(i,pn.x,pn.y,pn.z);return this}set(e,i=0){return this.array.set(e,i),this}getComponent(e,i){let r=this.array[e*this.itemSize+i];return this.normalized&&(r=Yo(r,this.array)),r}setComponent(e,i,r){return this.normalized&&(r=Wn(r,this.array)),this.array[e*this.itemSize+i]=r,this}getX(e){let i=this.array[e*this.itemSize];return this.normalized&&(i=Yo(i,this.array)),i}setX(e,i){return this.normalized&&(i=Wn(i,this.array)),this.array[e*this.itemSize]=i,this}getY(e){let i=this.array[e*this.itemSize+1];return this.normalized&&(i=Yo(i,this.array)),i}setY(e,i){return this.normalized&&(i=Wn(i,this.array)),this.array[e*this.itemSize+1]=i,this}getZ(e){let i=this.array[e*this.itemSize+2];return this.normalized&&(i=Yo(i,this.array)),i}setZ(e,i){return this.normalized&&(i=Wn(i,this.array)),this.array[e*this.itemSize+2]=i,this}getW(e){let i=this.array[e*this.itemSize+3];return this.normalized&&(i=Yo(i,this.array)),i}setW(e,i){return this.normalized&&(i=Wn(i,this.array)),this.array[e*this.itemSize+3]=i,this}setXY(e,i,r){return e*=this.itemSize,this.normalized&&(i=Wn(i,this.array),r=Wn(r,this.array)),this.array[e+0]=i,this.array[e+1]=r,this}setXYZ(e,i,r,l){return e*=this.itemSize,this.normalized&&(i=Wn(i,this.array),r=Wn(r,this.array),l=Wn(l,this.array)),this.array[e+0]=i,this.array[e+1]=r,this.array[e+2]=l,this}setXYZW(e,i,r,l,c){return e*=this.itemSize,this.normalized&&(i=Wn(i,this.array),r=Wn(r,this.array),l=Wn(l,this.array),c=Wn(c,this.array)),this.array[e+0]=i,this.array[e+1]=r,this.array[e+2]=l,this.array[e+3]=c,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){const e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return this.name!==""&&(e.name=this.name),this.usage!==O0&&(e.usage=this.usage),e}}class _x extends Yn{constructor(e,i,r){super(new Uint16Array(e),i,r)}}class vx extends Yn{constructor(e,i,r){super(new Uint32Array(e),i,r)}}class Aa extends Yn{constructor(e,i,r){super(new Float32Array(e),i,r)}}const Wb=new dl,Qo=new se,nd=new se;class xu{constructor(e=new se,i=-1){this.isSphere=!0,this.center=e,this.radius=i}set(e,i){return this.center.copy(e),this.radius=i,this}setFromPoints(e,i){const r=this.center;i!==void 0?r.copy(i):Wb.setFromPoints(e).getCenter(r);let l=0;for(let c=0,f=e.length;c<f;c++)l=Math.max(l,r.distanceToSquared(e[c]));return this.radius=Math.sqrt(l),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){const i=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=i*i}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,i){const r=this.center.distanceToSquared(e);return i.copy(e),r>this.radius*this.radius&&(i.sub(this.center).normalize(),i.multiplyScalar(this.radius).add(this.center)),i}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;Qo.subVectors(e,this.center);const i=Qo.lengthSq();if(i>this.radius*this.radius){const r=Math.sqrt(i),l=(r-this.radius)*.5;this.center.addScaledVector(Qo,l/r),this.radius+=l}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(nd.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(Qo.copy(e.center).add(nd)),this.expandByPoint(Qo.copy(e.center).sub(nd))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}}let qb=0;const vi=new nn,id=new Kn,zr=new se,oi=new dl,Jo=new dl,Mn=new se;class Fi extends Xs{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:qb++}),this.uuid=hl(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(Tb(e)?vx:_x)(e,1):this.index=e,this}setIndirect(e,i=0){return this.indirect=e,this.indirectOffset=i,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,i){return this.attributes[e]=i,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,i,r=0){this.groups.push({start:e,count:i,materialIndex:r})}clearGroups(){this.groups=[]}setDrawRange(e,i){this.drawRange.start=e,this.drawRange.count=i}applyMatrix4(e){const i=this.attributes.position;i!==void 0&&(i.applyMatrix4(e),i.needsUpdate=!0);const r=this.attributes.normal;if(r!==void 0){const c=new dt().getNormalMatrix(e);r.applyNormalMatrix(c),r.needsUpdate=!0}const l=this.attributes.tangent;return l!==void 0&&(l.transformDirection(e),l.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}applyQuaternion(e){return vi.makeRotationFromQuaternion(e),this.applyMatrix4(vi),this}rotateX(e){return vi.makeRotationX(e),this.applyMatrix4(vi),this}rotateY(e){return vi.makeRotationY(e),this.applyMatrix4(vi),this}rotateZ(e){return vi.makeRotationZ(e),this.applyMatrix4(vi),this}translate(e,i,r){return vi.makeTranslation(e,i,r),this.applyMatrix4(vi),this}scale(e,i,r){return vi.makeScale(e,i,r),this.applyMatrix4(vi),this}lookAt(e){return id.lookAt(e),id.updateMatrix(),this.applyMatrix4(id.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(zr).negate(),this.translate(zr.x,zr.y,zr.z),this}setFromPoints(e){const i=this.getAttribute("position");if(i===void 0){const r=[];for(let l=0,c=e.length;l<c;l++){const f=e[l];r.push(f.x,f.y,f.z||0)}this.setAttribute("position",new Aa(r,3))}else{const r=Math.min(e.length,i.count);for(let l=0;l<r;l++){const c=e[l];i.setXYZ(l,c.x,c.y,c.z||0)}e.length>i.count&&st("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),i.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new dl);const e=this.attributes.position,i=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){At("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new se(-1/0,-1/0,-1/0),new se(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),i)for(let r=0,l=i.length;r<l;r++){const c=i[r];oi.setFromBufferAttribute(c),this.morphTargetsRelative?(Mn.addVectors(this.boundingBox.min,oi.min),this.boundingBox.expandByPoint(Mn),Mn.addVectors(this.boundingBox.max,oi.max),this.boundingBox.expandByPoint(Mn)):(this.boundingBox.expandByPoint(oi.min),this.boundingBox.expandByPoint(oi.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&At('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new xu);const e=this.attributes.position,i=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){At("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new se,1/0);return}if(e){const r=this.boundingSphere.center;if(oi.setFromBufferAttribute(e),i)for(let c=0,f=i.length;c<f;c++){const p=i[c];Jo.setFromBufferAttribute(p),this.morphTargetsRelative?(Mn.addVectors(oi.min,Jo.min),oi.expandByPoint(Mn),Mn.addVectors(oi.max,Jo.max),oi.expandByPoint(Mn)):(oi.expandByPoint(Jo.min),oi.expandByPoint(Jo.max))}oi.getCenter(r);let l=0;for(let c=0,f=e.count;c<f;c++)Mn.fromBufferAttribute(e,c),l=Math.max(l,r.distanceToSquared(Mn));if(i)for(let c=0,f=i.length;c<f;c++){const p=i[c],m=this.morphTargetsRelative;for(let d=0,_=p.count;d<_;d++)Mn.fromBufferAttribute(p,d),m&&(zr.fromBufferAttribute(e,d),Mn.add(zr)),l=Math.max(l,r.distanceToSquared(Mn))}this.boundingSphere.radius=Math.sqrt(l),isNaN(this.boundingSphere.radius)&&At('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){const e=this.index,i=this.attributes;if(e===null||i.position===void 0||i.normal===void 0||i.uv===void 0){At("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}const r=i.position,l=i.normal,c=i.uv;this.hasAttribute("tangent")===!1&&this.setAttribute("tangent",new Yn(new Float32Array(4*r.count),4));const f=this.getAttribute("tangent"),p=[],m=[];for(let A=0;A<r.count;A++)p[A]=new se,m[A]=new se;const d=new se,_=new se,v=new se,g=new mt,M=new mt,E=new mt,R=new se,x=new se;function y(A,L,pe){d.fromBufferAttribute(r,A),_.fromBufferAttribute(r,L),v.fromBufferAttribute(r,pe),g.fromBufferAttribute(c,A),M.fromBufferAttribute(c,L),E.fromBufferAttribute(c,pe),_.sub(d),v.sub(d),M.sub(g),E.sub(g);const w=1/(M.x*E.y-E.x*M.y);isFinite(w)&&(R.copy(_).multiplyScalar(E.y).addScaledVector(v,-M.y).multiplyScalar(w),x.copy(v).multiplyScalar(M.x).addScaledVector(_,-E.x).multiplyScalar(w),p[A].add(R),p[L].add(R),p[pe].add(R),m[A].add(x),m[L].add(x),m[pe].add(x))}let T=this.groups;T.length===0&&(T=[{start:0,count:e.count}]);for(let A=0,L=T.length;A<L;++A){const pe=T[A],w=pe.start,Y=pe.count;for(let re=w,fe=w+Y;re<fe;re+=3)y(e.getX(re+0),e.getX(re+1),e.getX(re+2))}const U=new se,P=new se,V=new se,H=new se;function z(A){V.fromBufferAttribute(l,A),H.copy(V);const L=p[A];U.copy(L),U.sub(V.multiplyScalar(V.dot(L))).normalize(),P.crossVectors(H,L);const w=P.dot(m[A])<0?-1:1;f.setXYZW(A,U.x,U.y,U.z,w)}for(let A=0,L=T.length;A<L;++A){const pe=T[A],w=pe.start,Y=pe.count;for(let re=w,fe=w+Y;re<fe;re+=3)z(e.getX(re+0)),z(e.getX(re+1)),z(e.getX(re+2))}}computeVertexNormals(){const e=this.index,i=this.getAttribute("position");if(i!==void 0){let r=this.getAttribute("normal");if(r===void 0)r=new Yn(new Float32Array(i.count*3),3),this.setAttribute("normal",r);else for(let g=0,M=r.count;g<M;g++)r.setXYZ(g,0,0,0);const l=new se,c=new se,f=new se,p=new se,m=new se,d=new se,_=new se,v=new se;if(e)for(let g=0,M=e.count;g<M;g+=3){const E=e.getX(g+0),R=e.getX(g+1),x=e.getX(g+2);l.fromBufferAttribute(i,E),c.fromBufferAttribute(i,R),f.fromBufferAttribute(i,x),_.subVectors(f,c),v.subVectors(l,c),_.cross(v),p.fromBufferAttribute(r,E),m.fromBufferAttribute(r,R),d.fromBufferAttribute(r,x),p.add(_),m.add(_),d.add(_),r.setXYZ(E,p.x,p.y,p.z),r.setXYZ(R,m.x,m.y,m.z),r.setXYZ(x,d.x,d.y,d.z)}else for(let g=0,M=i.count;g<M;g+=3)l.fromBufferAttribute(i,g+0),c.fromBufferAttribute(i,g+1),f.fromBufferAttribute(i,g+2),_.subVectors(f,c),v.subVectors(l,c),_.cross(v),r.setXYZ(g+0,_.x,_.y,_.z),r.setXYZ(g+1,_.x,_.y,_.z),r.setXYZ(g+2,_.x,_.y,_.z);this.normalizeNormals(),r.needsUpdate=!0}}normalizeNormals(){const e=this.attributes.normal;for(let i=0,r=e.count;i<r;i++)Mn.fromBufferAttribute(e,i),Mn.normalize(),e.setXYZ(i,Mn.x,Mn.y,Mn.z)}toNonIndexed(){function e(p,m){const d=p.array,_=p.itemSize,v=p.normalized,g=new d.constructor(m.length*_);let M=0,E=0;for(let R=0,x=m.length;R<x;R++){p.isInterleavedBufferAttribute?M=m[R]*p.data.stride+p.offset:M=m[R]*_;for(let y=0;y<_;y++)g[E++]=d[M++]}return new Yn(g,_,v)}if(this.index===null)return st("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;const i=new Fi,r=this.index.array,l=this.attributes;for(const p in l){const m=l[p],d=e(m,r);i.setAttribute(p,d)}const c=this.morphAttributes;for(const p in c){const m=[],d=c[p];for(let _=0,v=d.length;_<v;_++){const g=d[_],M=e(g,r);m.push(M)}i.morphAttributes[p]=m}i.morphTargetsRelative=this.morphTargetsRelative;const f=this.groups;for(let p=0,m=f.length;p<m;p++){const d=f[p];i.addGroup(d.start,d.count,d.materialIndex)}return i}toJSON(){const e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.type,this.name!==""&&(e.name=this.name),Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0){const m=this.parameters;for(const d in m)m[d]!==void 0&&(e[d]=m[d]);return e}e.data={attributes:{}};const i=this.index;i!==null&&(e.data.index={type:i.array.constructor.name,array:Array.prototype.slice.call(i.array)});const r=this.attributes;for(const m in r){const d=r[m];e.data.attributes[m]=d.toJSON(e.data)}const l={};let c=!1;for(const m in this.morphAttributes){const d=this.morphAttributes[m],_=[];for(let v=0,g=d.length;v<g;v++){const M=d[v];_.push(M.toJSON(e.data))}_.length>0&&(l[m]=_,c=!0)}c&&(e.data.morphAttributes=l,e.data.morphTargetsRelative=this.morphTargetsRelative);const f=this.groups;f.length>0&&(e.data.groups=JSON.parse(JSON.stringify(f)));const p=this.boundingSphere;return p!==null&&(e.data.boundingSphere=p.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;const i={};this.name=e.name;const r=e.index;r!==null&&this.setIndex(r.clone());const l=e.attributes;for(const d in l){const _=l[d];this.setAttribute(d,_.clone(i))}const c=e.morphAttributes;for(const d in c){const _=[],v=c[d];for(let g=0,M=v.length;g<M;g++)_.push(v[g].clone(i));this.morphAttributes[d]=_}this.morphTargetsRelative=e.morphTargetsRelative;const f=e.groups;for(let d=0,_=f.length;d<_;d++){const v=f[d];this.addGroup(v.start,v.count,v.materialIndex)}const p=e.boundingBox;p!==null&&(this.boundingBox=p.clone());const m=e.boundingSphere;return m!==null&&(this.boundingSphere=m.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}}let Yb=0;class pl extends Xs{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:Yb++}),this.uuid=hl(),this.name="",this.type="Material",this.blending=jr,this.side=ds,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=xd,this.blendDst=yd,this.blendEquation=Hs,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new Lt(0,0,0),this.blendAlpha=0,this.depthFunc=Wr,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=L0,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=Cr,this.stencilZFail=Cr,this.stencilZPass=Cr,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(const i in e){const r=e[i];if(r===void 0){st(`Material: parameter '${i}' has value of undefined.`);continue}const l=this[i];if(l===void 0){st(`Material: '${i}' is not a property of THREE.${this.type}.`);continue}l&&l.isColor?l.set(r):l&&l.isVector3&&r&&r.isVector3?l.copy(r):this[i]=r}}toJSON(e){const i=e===void 0||typeof e=="string";i&&(e={textures:{},images:{}});const r={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};r.uuid=this.uuid,r.type=this.type,this.name!==""&&(r.name=this.name),this.color&&this.color.isColor&&(r.color=this.color.getHex()),this.roughness!==void 0&&(r.roughness=this.roughness),this.metalness!==void 0&&(r.metalness=this.metalness),this.sheen!==void 0&&(r.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(r.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(r.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(r.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1&&(r.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(r.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(r.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(r.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(r.shininess=this.shininess),this.clearcoat!==void 0&&(r.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(r.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(r.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(r.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(r.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,r.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(r.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(r.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(r.dispersion=this.dispersion),this.iridescence!==void 0&&(r.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(r.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(r.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(r.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(r.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(r.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(r.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(r.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(r.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(r.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(r.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(r.lightMap=this.lightMap.toJSON(e).uuid,r.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(r.aoMap=this.aoMap.toJSON(e).uuid,r.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(r.bumpMap=this.bumpMap.toJSON(e).uuid,r.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(r.normalMap=this.normalMap.toJSON(e).uuid,r.normalMapType=this.normalMapType,r.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(r.displacementMap=this.displacementMap.toJSON(e).uuid,r.displacementScale=this.displacementScale,r.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(r.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(r.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(r.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(r.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(r.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(r.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(r.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(r.combine=this.combine)),this.envMapRotation!==void 0&&(r.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(r.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(r.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(r.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(r.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(r.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(r.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(r.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(r.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0&&(r.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(r.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(r.size=this.size),this.shadowSide!==null&&(r.shadowSide=this.shadowSide),this.sizeAttenuation!==void 0&&(r.sizeAttenuation=this.sizeAttenuation),this.blending!==jr&&(r.blending=this.blending),this.side!==ds&&(r.side=this.side),this.vertexColors===!0&&(r.vertexColors=!0),this.opacity<1&&(r.opacity=this.opacity),this.transparent===!0&&(r.transparent=!0),this.blendSrc!==xd&&(r.blendSrc=this.blendSrc),this.blendDst!==yd&&(r.blendDst=this.blendDst),this.blendEquation!==Hs&&(r.blendEquation=this.blendEquation),this.blendSrcAlpha!==null&&(r.blendSrcAlpha=this.blendSrcAlpha),this.blendDstAlpha!==null&&(r.blendDstAlpha=this.blendDstAlpha),this.blendEquationAlpha!==null&&(r.blendEquationAlpha=this.blendEquationAlpha),this.blendColor&&this.blendColor.isColor&&(r.blendColor=this.blendColor.getHex()),this.blendAlpha!==0&&(r.blendAlpha=this.blendAlpha),this.depthFunc!==Wr&&(r.depthFunc=this.depthFunc),this.depthTest===!1&&(r.depthTest=this.depthTest),this.depthWrite===!1&&(r.depthWrite=this.depthWrite),this.colorWrite===!1&&(r.colorWrite=this.colorWrite),this.stencilWriteMask!==255&&(r.stencilWriteMask=this.stencilWriteMask),this.stencilFunc!==L0&&(r.stencilFunc=this.stencilFunc),this.stencilRef!==0&&(r.stencilRef=this.stencilRef),this.stencilFuncMask!==255&&(r.stencilFuncMask=this.stencilFuncMask),this.stencilFail!==Cr&&(r.stencilFail=this.stencilFail),this.stencilZFail!==Cr&&(r.stencilZFail=this.stencilZFail),this.stencilZPass!==Cr&&(r.stencilZPass=this.stencilZPass),this.stencilWrite===!0&&(r.stencilWrite=this.stencilWrite),this.rotation!==void 0&&this.rotation!==0&&(r.rotation=this.rotation),this.polygonOffset===!0&&(r.polygonOffset=!0),this.polygonOffsetFactor!==0&&(r.polygonOffsetFactor=this.polygonOffsetFactor),this.polygonOffsetUnits!==0&&(r.polygonOffsetUnits=this.polygonOffsetUnits),this.linewidth!==void 0&&this.linewidth!==1&&(r.linewidth=this.linewidth),this.dashSize!==void 0&&(r.dashSize=this.dashSize),this.gapSize!==void 0&&(r.gapSize=this.gapSize),this.scale!==void 0&&(r.scale=this.scale),this.dithering===!0&&(r.dithering=!0),this.alphaTest>0&&(r.alphaTest=this.alphaTest),this.alphaHash===!0&&(r.alphaHash=!0),this.alphaToCoverage===!0&&(r.alphaToCoverage=!0),this.premultipliedAlpha===!0&&(r.premultipliedAlpha=!0),this.forceSinglePass===!0&&(r.forceSinglePass=!0),this.allowOverride===!1&&(r.allowOverride=!1),this.wireframe===!0&&(r.wireframe=!0),this.wireframeLinewidth>1&&(r.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!=="round"&&(r.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!=="round"&&(r.wireframeLinejoin=this.wireframeLinejoin),this.flatShading===!0&&(r.flatShading=!0),this.visible===!1&&(r.visible=!1),this.toneMapped===!1&&(r.toneMapped=!1),this.fog===!1&&(r.fog=!1),Object.keys(this.userData).length>0&&(r.userData=this.userData);function l(c){const f=[];for(const p in c){const m=c[p];delete m.metadata,f.push(m)}return f}if(i){const c=l(e.textures),f=l(e.images);c.length>0&&(r.textures=c),f.length>0&&(r.images=f)}return r}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;const i=e.clippingPlanes;let r=null;if(i!==null){const l=i.length;r=new Array(l);for(let c=0;c!==l;++c)r[c]=i[c].clone()}return this.clippingPlanes=r,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}}const ya=new se,ad=new se,Bc=new se,ls=new se,sd=new se,Hc=new se,rd=new se;class yu{constructor(e=new se,i=new se(0,0,-1)){this.origin=e,this.direction=i}set(e,i){return this.origin.copy(e),this.direction.copy(i),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,i){return i.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,ya)),this}closestPointToPoint(e,i){i.subVectors(e,this.origin);const r=i.dot(this.direction);return r<0?i.copy(this.origin):i.copy(this.origin).addScaledVector(this.direction,r)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){const i=ya.subVectors(e,this.origin).dot(this.direction);return i<0?this.origin.distanceToSquared(e):(ya.copy(this.origin).addScaledVector(this.direction,i),ya.distanceToSquared(e))}distanceSqToSegment(e,i,r,l){ad.copy(e).add(i).multiplyScalar(.5),Bc.copy(i).sub(e).normalize(),ls.copy(this.origin).sub(ad);const c=e.distanceTo(i)*.5,f=-this.direction.dot(Bc),p=ls.dot(this.direction),m=-ls.dot(Bc),d=ls.lengthSq(),_=Math.abs(1-f*f);let v,g,M,E;if(_>0)if(v=f*m-p,g=f*p-m,E=c*_,v>=0)if(g>=-E)if(g<=E){const R=1/_;v*=R,g*=R,M=v*(v+f*g+2*p)+g*(f*v+g+2*m)+d}else g=c,v=Math.max(0,-(f*g+p)),M=-v*v+g*(g+2*m)+d;else g=-c,v=Math.max(0,-(f*g+p)),M=-v*v+g*(g+2*m)+d;else g<=-E?(v=Math.max(0,-(-f*c+p)),g=v>0?-c:Math.min(Math.max(-c,-m),c),M=-v*v+g*(g+2*m)+d):g<=E?(v=0,g=Math.min(Math.max(-c,-m),c),M=g*(g+2*m)+d):(v=Math.max(0,-(f*c+p)),g=v>0?c:Math.min(Math.max(-c,-m),c),M=-v*v+g*(g+2*m)+d);else g=f>0?-c:c,v=Math.max(0,-(f*g+p)),M=-v*v+g*(g+2*m)+d;return r&&r.copy(this.origin).addScaledVector(this.direction,v),l&&l.copy(ad).addScaledVector(Bc,g),M}intersectSphere(e,i){ya.subVectors(e.center,this.origin);const r=ya.dot(this.direction),l=ya.dot(ya)-r*r,c=e.radius*e.radius;if(l>c)return null;const f=Math.sqrt(c-l),p=r-f,m=r+f;return m<0?null:p<0?this.at(m,i):this.at(p,i)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){const i=e.normal.dot(this.direction);if(i===0)return e.distanceToPoint(this.origin)===0?0:null;const r=-(this.origin.dot(e.normal)+e.constant)/i;return r>=0?r:null}intersectPlane(e,i){const r=this.distanceToPlane(e);return r===null?null:this.at(r,i)}intersectsPlane(e){const i=e.distanceToPoint(this.origin);return i===0||e.normal.dot(this.direction)*i<0}intersectBox(e,i){let r,l,c,f,p,m;const d=1/this.direction.x,_=1/this.direction.y,v=1/this.direction.z,g=this.origin;return d>=0?(r=(e.min.x-g.x)*d,l=(e.max.x-g.x)*d):(r=(e.max.x-g.x)*d,l=(e.min.x-g.x)*d),_>=0?(c=(e.min.y-g.y)*_,f=(e.max.y-g.y)*_):(c=(e.max.y-g.y)*_,f=(e.min.y-g.y)*_),r>f||c>l||((c>r||isNaN(r))&&(r=c),(f<l||isNaN(l))&&(l=f),v>=0?(p=(e.min.z-g.z)*v,m=(e.max.z-g.z)*v):(p=(e.max.z-g.z)*v,m=(e.min.z-g.z)*v),r>m||p>l)||((p>r||r!==r)&&(r=p),(m<l||l!==l)&&(l=m),l<0)?null:this.at(r>=0?r:l,i)}intersectsBox(e){return this.intersectBox(e,ya)!==null}intersectTriangle(e,i,r,l,c){sd.subVectors(i,e),Hc.subVectors(r,e),rd.crossVectors(sd,Hc);let f=this.direction.dot(rd),p;if(f>0){if(l)return null;p=1}else if(f<0)p=-1,f=-f;else return null;ls.subVectors(this.origin,e);const m=p*this.direction.dot(Hc.crossVectors(ls,Hc));if(m<0)return null;const d=p*this.direction.dot(sd.cross(ls));if(d<0||m+d>f)return null;const _=-p*ls.dot(rd);return _<0?null:this.at(_/f,c)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class xx extends pl{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new Lt(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new Da,this.combine=Jv,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}}const Z0=new nn,Fs=new yu,Gc=new xu,K0=new se,Vc=new se,kc=new se,jc=new se,od=new se,Xc=new se,Q0=new se,Wc=new se;class Na extends Kn{constructor(e=new Fi,i=new xx){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=i,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,i){return super.copy(e,i),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){const i=this.geometry.morphAttributes,r=Object.keys(i);if(r.length>0){const l=i[r[0]];if(l!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let c=0,f=l.length;c<f;c++){const p=l[c].name||String(c);this.morphTargetInfluences.push(0),this.morphTargetDictionary[p]=c}}}}getVertexPosition(e,i){const r=this.geometry,l=r.attributes.position,c=r.morphAttributes.position,f=r.morphTargetsRelative;i.fromBufferAttribute(l,e);const p=this.morphTargetInfluences;if(c&&p){Xc.set(0,0,0);for(let m=0,d=c.length;m<d;m++){const _=p[m],v=c[m];_!==0&&(od.fromBufferAttribute(v,e),f?Xc.addScaledVector(od,_):Xc.addScaledVector(od.sub(i),_))}i.add(Xc)}return i}raycast(e,i){const r=this.geometry,l=this.material,c=this.matrixWorld;l!==void 0&&(r.boundingSphere===null&&r.computeBoundingSphere(),Gc.copy(r.boundingSphere),Gc.applyMatrix4(c),Fs.copy(e.ray).recast(e.near),!(Gc.containsPoint(Fs.origin)===!1&&(Fs.intersectSphere(Gc,K0)===null||Fs.origin.distanceToSquared(K0)>(e.far-e.near)**2))&&(Z0.copy(c).invert(),Fs.copy(e.ray).applyMatrix4(Z0),!(r.boundingBox!==null&&Fs.intersectsBox(r.boundingBox)===!1)&&this._computeIntersections(e,i,Fs)))}_computeIntersections(e,i,r){let l;const c=this.geometry,f=this.material,p=c.index,m=c.attributes.position,d=c.attributes.uv,_=c.attributes.uv1,v=c.attributes.normal,g=c.groups,M=c.drawRange;if(p!==null)if(Array.isArray(f))for(let E=0,R=g.length;E<R;E++){const x=g[E],y=f[x.materialIndex],T=Math.max(x.start,M.start),U=Math.min(p.count,Math.min(x.start+x.count,M.start+M.count));for(let P=T,V=U;P<V;P+=3){const H=p.getX(P),z=p.getX(P+1),A=p.getX(P+2);l=qc(this,y,e,r,d,_,v,H,z,A),l&&(l.faceIndex=Math.floor(P/3),l.face.materialIndex=x.materialIndex,i.push(l))}}else{const E=Math.max(0,M.start),R=Math.min(p.count,M.start+M.count);for(let x=E,y=R;x<y;x+=3){const T=p.getX(x),U=p.getX(x+1),P=p.getX(x+2);l=qc(this,f,e,r,d,_,v,T,U,P),l&&(l.faceIndex=Math.floor(x/3),i.push(l))}}else if(m!==void 0)if(Array.isArray(f))for(let E=0,R=g.length;E<R;E++){const x=g[E],y=f[x.materialIndex],T=Math.max(x.start,M.start),U=Math.min(m.count,Math.min(x.start+x.count,M.start+M.count));for(let P=T,V=U;P<V;P+=3){const H=P,z=P+1,A=P+2;l=qc(this,y,e,r,d,_,v,H,z,A),l&&(l.faceIndex=Math.floor(P/3),l.face.materialIndex=x.materialIndex,i.push(l))}}else{const E=Math.max(0,M.start),R=Math.min(m.count,M.start+M.count);for(let x=E,y=R;x<y;x+=3){const T=x,U=x+1,P=x+2;l=qc(this,f,e,r,d,_,v,T,U,P),l&&(l.faceIndex=Math.floor(x/3),i.push(l))}}}}function Zb(s,e,i,r,l,c,f,p){let m;if(e.side===Zn?m=r.intersectTriangle(f,c,l,!0,p):m=r.intersectTriangle(l,c,f,e.side===ds,p),m===null)return null;Wc.copy(p),Wc.applyMatrix4(s.matrixWorld);const d=i.ray.origin.distanceTo(Wc);return d<i.near||d>i.far?null:{distance:d,point:Wc.clone(),object:s}}function qc(s,e,i,r,l,c,f,p,m,d){s.getVertexPosition(p,Vc),s.getVertexPosition(m,kc),s.getVertexPosition(d,jc);const _=Zb(s,e,i,r,Vc,kc,jc,Q0);if(_){const v=new se;Ui.getBarycoord(Q0,Vc,kc,jc,v),l&&(_.uv=Ui.getInterpolatedAttribute(l,p,m,d,v,new mt)),c&&(_.uv1=Ui.getInterpolatedAttribute(c,p,m,d,v,new mt)),f&&(_.normal=Ui.getInterpolatedAttribute(f,p,m,d,v,new se),_.normal.dot(r.direction)>0&&_.normal.multiplyScalar(-1));const g={a:p,b:m,c:d,normal:new se,materialIndex:0};Ui.getNormal(Vc,kc,jc,g.normal),_.face=g,_.barycoord=v}return _}class Kb extends Bn{constructor(e=null,i=1,r=1,l,c,f,p,m,d=Rn,_=Rn,v,g){super(null,f,p,m,d,_,l,c,v,g),this.isDataTexture=!0,this.image={data:e,width:i,height:r},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}const ld=new se,Qb=new se,Jb=new dt;class us{constructor(e=new se(1,0,0),i=0){this.isPlane=!0,this.normal=e,this.constant=i}set(e,i){return this.normal.copy(e),this.constant=i,this}setComponents(e,i,r,l){return this.normal.set(e,i,r),this.constant=l,this}setFromNormalAndCoplanarPoint(e,i){return this.normal.copy(e),this.constant=-i.dot(this.normal),this}setFromCoplanarPoints(e,i,r){const l=ld.subVectors(r,i).cross(Qb.subVectors(e,i)).normalize();return this.setFromNormalAndCoplanarPoint(l,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){const e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,i){return i.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,i){const r=e.delta(ld),l=this.normal.dot(r);if(l===0)return this.distanceToPoint(e.start)===0?i.copy(e.start):null;const c=-(e.start.dot(this.normal)+this.constant)/l;return c<0||c>1?null:i.copy(e.start).addScaledVector(r,c)}intersectsLine(e){const i=this.distanceToPoint(e.start),r=this.distanceToPoint(e.end);return i<0&&r>0||r<0&&i>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,i){const r=i||Jb.getNormalMatrix(e),l=this.coplanarPoint(ld).applyMatrix4(e),c=this.normal.applyMatrix3(r).normalize();return this.constant=-l.dot(c),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}}const Is=new xu,$b=new mt(.5,.5),Yc=new se;class yx{constructor(e=new us,i=new us,r=new us,l=new us,c=new us,f=new us){this.planes=[e,i,r,l,c,f]}set(e,i,r,l,c,f){const p=this.planes;return p[0].copy(e),p[1].copy(i),p[2].copy(r),p[3].copy(l),p[4].copy(c),p[5].copy(f),this}copy(e){const i=this.planes;for(let r=0;r<6;r++)i[r].copy(e.planes[r]);return this}setFromProjectionMatrix(e,i=Wi,r=!1){const l=this.planes,c=e.elements,f=c[0],p=c[1],m=c[2],d=c[3],_=c[4],v=c[5],g=c[6],M=c[7],E=c[8],R=c[9],x=c[10],y=c[11],T=c[12],U=c[13],P=c[14],V=c[15];if(l[0].setComponents(d-f,M-_,y-E,V-T).normalize(),l[1].setComponents(d+f,M+_,y+E,V+T).normalize(),l[2].setComponents(d+p,M+v,y+R,V+U).normalize(),l[3].setComponents(d-p,M-v,y-R,V-U).normalize(),r)l[4].setComponents(m,g,x,P).normalize(),l[5].setComponents(d-m,M-g,y-x,V-P).normalize();else if(l[4].setComponents(d-m,M-g,y-x,V-P).normalize(),i===Wi)l[5].setComponents(d+m,M+g,y+x,V+P).normalize();else if(i===du)l[5].setComponents(m,g,x,P).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+i);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),Is.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{const i=e.geometry;i.boundingSphere===null&&i.computeBoundingSphere(),Is.copy(i.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(Is)}intersectsSprite(e){Is.center.set(0,0,0);const i=$b.distanceTo(e.center);return Is.radius=.7071067811865476+i,Is.applyMatrix4(e.matrixWorld),this.intersectsSphere(Is)}intersectsSphere(e){const i=this.planes,r=e.center,l=-e.radius;for(let c=0;c<6;c++)if(i[c].distanceToPoint(r)<l)return!1;return!0}intersectsBox(e){const i=this.planes;for(let r=0;r<6;r++){const l=i[r];if(Yc.x=l.normal.x>0?e.max.x:e.min.x,Yc.y=l.normal.y>0?e.max.y:e.min.y,Yc.z=l.normal.z>0?e.max.z:e.min.z,l.distanceToPoint(Yc)<0)return!1}return!0}containsPoint(e){const i=this.planes;for(let r=0;r<6;r++)if(i[r].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class Sx extends pl{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new Lt(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}}const J0=new nn,cp=new yu,Zc=new xu,Kc=new se;class eT extends Kn{constructor(e=new Fi,i=new Sx){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=i,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,i){return super.copy(e,i),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}raycast(e,i){const r=this.geometry,l=this.matrixWorld,c=e.params.Points.threshold,f=r.drawRange;if(r.boundingSphere===null&&r.computeBoundingSphere(),Zc.copy(r.boundingSphere),Zc.applyMatrix4(l),Zc.radius+=c,e.ray.intersectsSphere(Zc)===!1)return;J0.copy(l).invert(),cp.copy(e.ray).applyMatrix4(J0);const p=c/((this.scale.x+this.scale.y+this.scale.z)/3),m=p*p,d=r.index,v=r.attributes.position;if(d!==null){const g=Math.max(0,f.start),M=Math.min(d.count,f.start+f.count);for(let E=g,R=M;E<R;E++){const x=d.getX(E);Kc.fromBufferAttribute(v,x),$0(Kc,x,m,l,e,i,this)}}else{const g=Math.max(0,f.start),M=Math.min(v.count,f.start+f.count);for(let E=g,R=M;E<R;E++)Kc.fromBufferAttribute(v,E),$0(Kc,E,m,l,e,i,this)}}updateMorphTargets(){const i=this.geometry.morphAttributes,r=Object.keys(i);if(r.length>0){const l=i[r[0]];if(l!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let c=0,f=l.length;c<f;c++){const p=l[c].name||String(c);this.morphTargetInfluences.push(0),this.morphTargetDictionary[p]=c}}}}}function $0(s,e,i,r,l,c,f){const p=cp.distanceSqToPoint(s);if(p<i){const m=new se;cp.closestPointToPoint(s,m),m.applyMatrix4(r);const d=l.ray.origin.distanceTo(m);if(d<l.near||d>l.far)return;c.push({distance:d,distanceToRay:Math.sqrt(p),point:m,index:e,face:null,faceIndex:null,barycoord:null,object:f})}}class Mx extends Bn{constructor(e=[],i=js,r,l,c,f,p,m,d,_){super(e,i,r,l,c,f,p,m,d,_),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}}class cl extends Bn{constructor(e,i,r=Zi,l,c,f,p=Rn,m=Rn,d,_=wa,v=1){if(_!==wa&&_!==ks)throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");const g={width:e,height:i,depth:v};super(g,l,c,f,p,m,_,r,d),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new Dp(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){const i=super.toJSON(e);return this.compareFunction!==null&&(i.compareFunction=this.compareFunction),i}}class tT extends cl{constructor(e,i=Zi,r=js,l,c,f=Rn,p=Rn,m,d=wa){const _={width:e,height:e,depth:1},v=[_,_,_,_,_,_];super(e,e,i,r,l,c,f,p,m,d),this.image=v,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}}class Ex extends Bn{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}}class ml extends Fi{constructor(e=1,i=1,r=1,l=1,c=1,f=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:i,depth:r,widthSegments:l,heightSegments:c,depthSegments:f};const p=this;l=Math.floor(l),c=Math.floor(c),f=Math.floor(f);const m=[],d=[],_=[],v=[];let g=0,M=0;E("z","y","x",-1,-1,r,i,e,f,c,0),E("z","y","x",1,-1,r,i,-e,f,c,1),E("x","z","y",1,1,e,r,i,l,f,2),E("x","z","y",1,-1,e,r,-i,l,f,3),E("x","y","z",1,-1,e,i,r,l,c,4),E("x","y","z",-1,-1,e,i,-r,l,c,5),this.setIndex(m),this.setAttribute("position",new Aa(d,3)),this.setAttribute("normal",new Aa(_,3)),this.setAttribute("uv",new Aa(v,2));function E(R,x,y,T,U,P,V,H,z,A,L){const pe=P/z,w=V/A,Y=P/2,re=V/2,fe=H/2,ee=z+1,I=A+1;let B=0,$=0;const Q=new se;for(let de=0;de<I;de++){const O=de*w-re;for(let j=0;j<ee;j++){const ve=j*pe-Y;Q[R]=ve*T,Q[x]=O*U,Q[y]=fe,d.push(Q.x,Q.y,Q.z),Q[R]=0,Q[x]=0,Q[y]=H>0?1:-1,_.push(Q.x,Q.y,Q.z),v.push(j/z),v.push(1-de/A),B+=1}}for(let de=0;de<A;de++)for(let O=0;O<z;O++){const j=g+O+ee*de,ve=g+O+ee*(de+1),he=g+(O+1)+ee*(de+1),Ne=g+(O+1)+ee*de;m.push(j,ve,Ne),m.push(ve,he,Ne),$+=6}p.addGroup(M,$,L),M+=$,g+=B}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new ml(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}}class Su extends Fi{constructor(e=1,i=1,r=1,l=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:i,widthSegments:r,heightSegments:l};const c=e/2,f=i/2,p=Math.floor(r),m=Math.floor(l),d=p+1,_=m+1,v=e/p,g=i/m,M=[],E=[],R=[],x=[];for(let y=0;y<_;y++){const T=y*g-f;for(let U=0;U<d;U++){const P=U*v-c;E.push(P,-T,0),R.push(0,0,1),x.push(U/p),x.push(1-y/m)}}for(let y=0;y<m;y++)for(let T=0;T<p;T++){const U=T+d*y,P=T+d*(y+1),V=T+1+d*(y+1),H=T+1+d*y;M.push(U,P,H),M.push(P,V,H)}this.setIndex(M),this.setAttribute("position",new Aa(E,3)),this.setAttribute("normal",new Aa(R,3)),this.setAttribute("uv",new Aa(x,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Su(e.width,e.height,e.widthSegments,e.heightSegments)}}function Kr(s){const e={};for(const i in s){e[i]={};for(const r in s[i]){const l=s[i][r];l&&(l.isColor||l.isMatrix3||l.isMatrix4||l.isVector2||l.isVector3||l.isVector4||l.isTexture||l.isQuaternion)?l.isRenderTargetTexture?(st("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[i][r]=null):e[i][r]=l.clone():Array.isArray(l)?e[i][r]=l.slice():e[i][r]=l}}return e}function zn(s){const e={};for(let i=0;i<s.length;i++){const r=Kr(s[i]);for(const l in r)e[l]=r[l]}return e}function nT(s){const e=[];for(let i=0;i<s.length;i++)e.push(s[i].clone());return e}function bx(s){const e=s.getRenderTarget();return e===null?s.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:Rt.workingColorSpace}const iT={clone:Kr,merge:zn};var aT=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,sT=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class Ki extends pl{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=aT,this.fragmentShader=sT,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Kr(e.uniforms),this.uniformsGroups=nT(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){const i=super.toJSON(e);i.glslVersion=this.glslVersion,i.uniforms={};for(const l in this.uniforms){const f=this.uniforms[l].value;f&&f.isTexture?i.uniforms[l]={type:"t",value:f.toJSON(e).uuid}:f&&f.isColor?i.uniforms[l]={type:"c",value:f.getHex()}:f&&f.isVector2?i.uniforms[l]={type:"v2",value:f.toArray()}:f&&f.isVector3?i.uniforms[l]={type:"v3",value:f.toArray()}:f&&f.isVector4?i.uniforms[l]={type:"v4",value:f.toArray()}:f&&f.isMatrix3?i.uniforms[l]={type:"m3",value:f.toArray()}:f&&f.isMatrix4?i.uniforms[l]={type:"m4",value:f.toArray()}:i.uniforms[l]={value:f}}Object.keys(this.defines).length>0&&(i.defines=this.defines),i.vertexShader=this.vertexShader,i.fragmentShader=this.fragmentShader,i.lights=this.lights,i.clipping=this.clipping;const r={};for(const l in this.extensions)this.extensions[l]===!0&&(r[l]=!0);return Object.keys(r).length>0&&(i.extensions=r),i}}class rT extends Ki{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}}class oT extends pl{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=gb,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}}class lT extends pl{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}}const Qc=new se,Jc=new ps,Vi=new se;class Tx extends Kn{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new nn,this.projectionMatrix=new nn,this.projectionMatrixInverse=new nn,this.coordinateSystem=Wi,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,i){return super.copy(e,i),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorld.decompose(Qc,Jc,Vi),Vi.x===1&&Vi.y===1&&Vi.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Qc,Jc,Vi.set(1,1,1)).invert()}updateWorldMatrix(e,i){super.updateWorldMatrix(e,i),this.matrixWorld.decompose(Qc,Jc,Vi),Vi.x===1&&Vi.y===1&&Vi.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Qc,Jc,Vi.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}}const cs=new se,ev=new mt,tv=new mt;class yi extends Tx{constructor(e=50,i=1,r=.1,l=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=r,this.far=l,this.focus=10,this.aspect=i,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,i){return super.copy(e,i),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){const i=.5*this.getFilmHeight()/e;this.fov=lp*2*Math.atan(i),this.updateProjectionMatrix()}getFocalLength(){const e=Math.tan(cu*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return lp*2*Math.atan(Math.tan(cu*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,i,r){cs.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),i.set(cs.x,cs.y).multiplyScalar(-e/cs.z),cs.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),r.set(cs.x,cs.y).multiplyScalar(-e/cs.z)}getViewSize(e,i){return this.getViewBounds(e,ev,tv),i.subVectors(tv,ev)}setViewOffset(e,i,r,l,c,f){this.aspect=e/i,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=i,this.view.offsetX=r,this.view.offsetY=l,this.view.width=c,this.view.height=f,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=this.near;let i=e*Math.tan(cu*.5*this.fov)/this.zoom,r=2*i,l=this.aspect*r,c=-.5*l;const f=this.view;if(this.view!==null&&this.view.enabled){const m=f.fullWidth,d=f.fullHeight;c+=f.offsetX*l/m,i-=f.offsetY*r/d,l*=f.width/m,r*=f.height/d}const p=this.filmOffset;p!==0&&(c+=e*p/this.getFilmWidth()),this.projectionMatrix.makePerspective(c,c+l,i,i-r,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const i=super.toJSON(e);return i.object.fov=this.fov,i.object.zoom=this.zoom,i.object.near=this.near,i.object.far=this.far,i.object.focus=this.focus,i.object.aspect=this.aspect,this.view!==null&&(i.object.view=Object.assign({},this.view)),i.object.filmGauge=this.filmGauge,i.object.filmOffset=this.filmOffset,i}}class Ax extends Tx{constructor(e=-1,i=1,r=1,l=-1,c=.1,f=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=i,this.top=r,this.bottom=l,this.near=c,this.far=f,this.updateProjectionMatrix()}copy(e,i){return super.copy(e,i),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,i,r,l,c,f){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=i,this.view.offsetX=r,this.view.offsetY=l,this.view.width=c,this.view.height=f,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=(this.right-this.left)/(2*this.zoom),i=(this.top-this.bottom)/(2*this.zoom),r=(this.right+this.left)/2,l=(this.top+this.bottom)/2;let c=r-e,f=r+e,p=l+i,m=l-i;if(this.view!==null&&this.view.enabled){const d=(this.right-this.left)/this.view.fullWidth/this.zoom,_=(this.top-this.bottom)/this.view.fullHeight/this.zoom;c+=d*this.view.offsetX,f=c+d*this.view.width,p-=_*this.view.offsetY,m=p-_*this.view.height}this.projectionMatrix.makeOrthographic(c,f,p,m,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const i=super.toJSON(e);return i.object.zoom=this.zoom,i.object.left=this.left,i.object.right=this.right,i.object.top=this.top,i.object.bottom=this.bottom,i.object.near=this.near,i.object.far=this.far,this.view!==null&&(i.object.view=Object.assign({},this.view)),i}}const Br=-90,Hr=1;class cT extends Kn{constructor(e,i,r){super(),this.type="CubeCamera",this.renderTarget=r,this.coordinateSystem=null,this.activeMipmapLevel=0;const l=new yi(Br,Hr,e,i);l.layers=this.layers,this.add(l);const c=new yi(Br,Hr,e,i);c.layers=this.layers,this.add(c);const f=new yi(Br,Hr,e,i);f.layers=this.layers,this.add(f);const p=new yi(Br,Hr,e,i);p.layers=this.layers,this.add(p);const m=new yi(Br,Hr,e,i);m.layers=this.layers,this.add(m);const d=new yi(Br,Hr,e,i);d.layers=this.layers,this.add(d)}updateCoordinateSystem(){const e=this.coordinateSystem,i=this.children.concat(),[r,l,c,f,p,m]=i;for(const d of i)this.remove(d);if(e===Wi)r.up.set(0,1,0),r.lookAt(1,0,0),l.up.set(0,1,0),l.lookAt(-1,0,0),c.up.set(0,0,-1),c.lookAt(0,1,0),f.up.set(0,0,1),f.lookAt(0,-1,0),p.up.set(0,1,0),p.lookAt(0,0,1),m.up.set(0,1,0),m.lookAt(0,0,-1);else if(e===du)r.up.set(0,-1,0),r.lookAt(-1,0,0),l.up.set(0,-1,0),l.lookAt(1,0,0),c.up.set(0,0,1),c.lookAt(0,1,0),f.up.set(0,0,-1),f.lookAt(0,-1,0),p.up.set(0,-1,0),p.lookAt(0,0,1),m.up.set(0,-1,0),m.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(const d of i)this.add(d),d.updateMatrixWorld()}update(e,i){this.parent===null&&this.updateMatrixWorld();const{renderTarget:r,activeMipmapLevel:l}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());const[c,f,p,m,d,_]=this.children,v=e.getRenderTarget(),g=e.getActiveCubeFace(),M=e.getActiveMipmapLevel(),E=e.xr.enabled;e.xr.enabled=!1;const R=r.texture.generateMipmaps;r.texture.generateMipmaps=!1;let x=!1;e.isWebGLRenderer===!0?x=e.state.buffers.depth.getReversed():x=e.reversedDepthBuffer,e.setRenderTarget(r,0,l),x&&e.autoClear===!1&&e.clearDepth(),e.render(i,c),e.setRenderTarget(r,1,l),x&&e.autoClear===!1&&e.clearDepth(),e.render(i,f),e.setRenderTarget(r,2,l),x&&e.autoClear===!1&&e.clearDepth(),e.render(i,p),e.setRenderTarget(r,3,l),x&&e.autoClear===!1&&e.clearDepth(),e.render(i,m),e.setRenderTarget(r,4,l),x&&e.autoClear===!1&&e.clearDepth(),e.render(i,d),r.texture.generateMipmaps=R,e.setRenderTarget(r,5,l),x&&e.autoClear===!1&&e.clearDepth(),e.render(i,_),e.setRenderTarget(v,g,M),e.xr.enabled=E,r.texture.needsPMREMUpdate=!0}}class uT extends yi{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}}const nv=new nn;class fT{constructor(e,i,r=0,l=1/0){this.ray=new yu(e,i),this.near=r,this.far=l,this.camera=null,this.layers=new Np,this.params={Mesh:{},Line:{threshold:1},LOD:{},Points:{threshold:1},Sprite:{}}}set(e,i){this.ray.set(e,i)}setFromCamera(e,i){i.isPerspectiveCamera?(this.ray.origin.setFromMatrixPosition(i.matrixWorld),this.ray.direction.set(e.x,e.y,.5).unproject(i).sub(this.ray.origin).normalize(),this.camera=i):i.isOrthographicCamera?(this.ray.origin.set(e.x,e.y,(i.near+i.far)/(i.near-i.far)).unproject(i),this.ray.direction.set(0,0,-1).transformDirection(i.matrixWorld),this.camera=i):At("Raycaster: Unsupported camera type: "+i.type)}setFromXRController(e){return nv.identity().extractRotation(e.matrixWorld),this.ray.origin.setFromMatrixPosition(e.matrixWorld),this.ray.direction.set(0,0,-1).applyMatrix4(nv),this}intersectObject(e,i=!0,r=[]){return up(e,this,r,i),r.sort(iv),r}intersectObjects(e,i=!0,r=[]){for(let l=0,c=e.length;l<c;l++)up(e[l],this,r,i);return r.sort(iv),r}}function iv(s,e){return s.distance-e.distance}function up(s,e,i,r){let l=!0;if(s.layers.test(e.layers)&&s.raycast(e,i)===!1&&(l=!1),l===!0&&r===!0){const c=s.children;for(let f=0,p=c.length;f<p;f++)up(c[f],e,i,!0)}}class av{constructor(e=1,i=0,r=0){this.radius=e,this.phi=i,this.theta=r}set(e,i,r){return this.radius=e,this.phi=i,this.theta=r,this}copy(e){return this.radius=e.radius,this.phi=e.phi,this.theta=e.theta,this}makeSafe(){return this.phi=xt(this.phi,1e-6,Math.PI-1e-6),this}setFromVector3(e){return this.setFromCartesianCoords(e.x,e.y,e.z)}setFromCartesianCoords(e,i,r){return this.radius=Math.sqrt(e*e+i*i+r*r),this.radius===0?(this.theta=0,this.phi=0):(this.theta=Math.atan2(e,r),this.phi=Math.acos(xt(i/this.radius,-1,1))),this}clone(){return new this.constructor().copy(this)}}class hT extends Xs{constructor(e,i=null){super(),this.object=e,this.domElement=i,this.enabled=!0,this.state=-1,this.keys={},this.mouseButtons={LEFT:null,MIDDLE:null,RIGHT:null},this.touches={ONE:null,TWO:null}}connect(e){if(e===void 0){st("Controls: connect() now requires an element.");return}this.domElement!==null&&this.disconnect(),this.domElement=e}disconnect(){}dispose(){}update(){}}function sv(s,e,i,r){const l=dT(r);switch(i){case fx:return s*e;case dx:return s*e/l.components*l.byteLength;case Tp:return s*e/l.components*l.byteLength;case Yr:return s*e*2/l.components*l.byteLength;case Ap:return s*e*2/l.components*l.byteLength;case hx:return s*e*3/l.components*l.byteLength;case Li:return s*e*4/l.components*l.byteLength;case Rp:return s*e*4/l.components*l.byteLength;case su:case ru:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*8;case ou:case lu:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*16;case Nd:case Ld:return Math.max(s,16)*Math.max(e,8)/4;case Dd:case Ud:return Math.max(s,8)*Math.max(e,8)/2;case Od:case Pd:case Id:case zd:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*8;case Fd:case Bd:case Hd:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*16;case Gd:return Math.floor((s+3)/4)*Math.floor((e+3)/4)*16;case Vd:return Math.floor((s+4)/5)*Math.floor((e+3)/4)*16;case kd:return Math.floor((s+4)/5)*Math.floor((e+4)/5)*16;case jd:return Math.floor((s+5)/6)*Math.floor((e+4)/5)*16;case Xd:return Math.floor((s+5)/6)*Math.floor((e+5)/6)*16;case Wd:return Math.floor((s+7)/8)*Math.floor((e+4)/5)*16;case qd:return Math.floor((s+7)/8)*Math.floor((e+5)/6)*16;case Yd:return Math.floor((s+7)/8)*Math.floor((e+7)/8)*16;case Zd:return Math.floor((s+9)/10)*Math.floor((e+4)/5)*16;case Kd:return Math.floor((s+9)/10)*Math.floor((e+5)/6)*16;case Qd:return Math.floor((s+9)/10)*Math.floor((e+7)/8)*16;case Jd:return Math.floor((s+9)/10)*Math.floor((e+9)/10)*16;case $d:return Math.floor((s+11)/12)*Math.floor((e+9)/10)*16;case ep:return Math.floor((s+11)/12)*Math.floor((e+11)/12)*16;case tp:case np:case ip:return Math.ceil(s/4)*Math.ceil(e/4)*16;case ap:case sp:return Math.ceil(s/4)*Math.ceil(e/4)*8;case rp:case op:return Math.ceil(s/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${i} format.`)}function dT(s){switch(s){case Si:case ox:return{byteLength:1,components:1};case ol:case lx:case Ca:return{byteLength:2,components:1};case Ep:case bp:return{byteLength:2,components:4};case Zi:case Mp:case Xi:return{byteLength:4,components:1};case cx:case ux:return{byteLength:4,components:3}}throw new Error(`Unknown texture type ${s}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:Sp}}));typeof window<"u"&&(window.__THREE__?st("WARNING: Multiple instances of Three.js being imported."):window.__THREE__=Sp);function Rx(){let s=null,e=!1,i=null,r=null;function l(c,f){i(c,f),r=s.requestAnimationFrame(l)}return{start:function(){e!==!0&&i!==null&&(r=s.requestAnimationFrame(l),e=!0)},stop:function(){s.cancelAnimationFrame(r),e=!1},setAnimationLoop:function(c){i=c},setContext:function(c){s=c}}}function pT(s){const e=new WeakMap;function i(p,m){const d=p.array,_=p.usage,v=d.byteLength,g=s.createBuffer();s.bindBuffer(m,g),s.bufferData(m,d,_),p.onUploadCallback();let M;if(d instanceof Float32Array)M=s.FLOAT;else if(typeof Float16Array<"u"&&d instanceof Float16Array)M=s.HALF_FLOAT;else if(d instanceof Uint16Array)p.isFloat16BufferAttribute?M=s.HALF_FLOAT:M=s.UNSIGNED_SHORT;else if(d instanceof Int16Array)M=s.SHORT;else if(d instanceof Uint32Array)M=s.UNSIGNED_INT;else if(d instanceof Int32Array)M=s.INT;else if(d instanceof Int8Array)M=s.BYTE;else if(d instanceof Uint8Array)M=s.UNSIGNED_BYTE;else if(d instanceof Uint8ClampedArray)M=s.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+d);return{buffer:g,type:M,bytesPerElement:d.BYTES_PER_ELEMENT,version:p.version,size:v}}function r(p,m,d){const _=m.array,v=m.updateRanges;if(s.bindBuffer(d,p),v.length===0)s.bufferSubData(d,0,_);else{v.sort((M,E)=>M.start-E.start);let g=0;for(let M=1;M<v.length;M++){const E=v[g],R=v[M];R.start<=E.start+E.count+1?E.count=Math.max(E.count,R.start+R.count-E.start):(++g,v[g]=R)}v.length=g+1;for(let M=0,E=v.length;M<E;M++){const R=v[M];s.bufferSubData(d,R.start*_.BYTES_PER_ELEMENT,_,R.start,R.count)}m.clearUpdateRanges()}m.onUploadCallback()}function l(p){return p.isInterleavedBufferAttribute&&(p=p.data),e.get(p)}function c(p){p.isInterleavedBufferAttribute&&(p=p.data);const m=e.get(p);m&&(s.deleteBuffer(m.buffer),e.delete(p))}function f(p,m){if(p.isInterleavedBufferAttribute&&(p=p.data),p.isGLBufferAttribute){const _=e.get(p);(!_||_.version<p.version)&&e.set(p,{buffer:p.buffer,type:p.type,bytesPerElement:p.elementSize,version:p.version});return}const d=e.get(p);if(d===void 0)e.set(p,i(p,m));else if(d.version<p.version){if(d.size!==p.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");r(d.buffer,p,m),d.version=p.version}}return{get:l,remove:c,update:f}}var mT=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,gT=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,_T=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,vT=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,xT=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,yT=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,ST=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,MT=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,ET=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec4 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 );
	}
#endif`,bT=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,TT=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,AT=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,RT=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,CT=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,wT=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,DT=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,NT=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,UT=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,LT=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,OT=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,PT=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,FT=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,IT=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec4( 1.0 );
#endif
#ifdef USE_COLOR_ALPHA
	vColor *= color;
#elif defined( USE_COLOR )
	vColor.rgb *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.rgb *= instanceColor.rgb;
#endif
#ifdef USE_BATCHING_COLOR
	vColor *= getBatchingColor( getIndirectIndex( gl_DrawID ) );
#endif`,zT=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
vec3 inverseTransformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( vec4( dir, 0.0 ) * matrix ).xyz );
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,BT=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,HT=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
	#ifdef FLIP_SIDED
		transformedTangent = - transformedTangent;
	#endif
#endif`,GT=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,VT=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,kT=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,jT=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,XT="gl_FragColor = linearToOutputTexel( gl_FragColor );",WT=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,qT=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * vec3( flipEnvMap * reflectVec.x, reflectVec.yz ) );
		#ifdef ENVMAP_BLENDING_MULTIPLY
			outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_MIX )
			outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_ADD )
			outgoingLight += envColor.xyz * specularStrength * reflectivity;
		#endif
	#endif
#endif`,YT=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform float flipEnvMap;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,ZT=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,KT=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,QT=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,JT=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,$T=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,eA=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,tA=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,nA=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,iA=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,aA=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,sA=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,rA=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif`,oA=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, pow4( roughness ) ) );
			reflectVec = inverseTransformDirection( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
#endif`,lA=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,cA=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,uA=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,fA=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,hA=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.diffuseContribution = diffuseColor.rgb * ( 1.0 - metalnessFactor );
material.metalness = metalnessFactor;
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor;
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = vec3( 0.04 );
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.0001, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,dA=`uniform sampler2D dfgLUT;
struct PhysicalMaterial {
	vec3 diffuseColor;
	vec3 diffuseContribution;
	vec3 specularColor;
	vec3 specularColorBlended;
	float roughness;
	float metalness;
	float specularF90;
	float dispersion;
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0;
		vec3 iridescenceFresnelDielectric;
		vec3 iridescenceFresnelMetallic;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		float v = 0.5 / ( gv + gl );
		return v;
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColorBlended;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transpose( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float rInv = 1.0 / ( roughness + 0.1 );
	float a = -1.9362 + 1.0678 * roughness + 0.4573 * r2 - 0.8469 * rInv;
	float b = -0.6014 + 0.5538 * roughness - 0.4670 * r2 - 0.1255 * rInv;
	float DG = exp( a * dotNV + b );
	return saturate( DG );
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
vec3 BRDF_GGX_Multiscatter( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 singleScatter = BRDF_GGX( lightDir, viewDir, normal, material );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 dfgV = texture2D( dfgLUT, vec2( material.roughness, dotNV ) ).rg;
	vec2 dfgL = texture2D( dfgLUT, vec2( material.roughness, dotNL ) ).rg;
	vec3 FssEss_V = material.specularColorBlended * dfgV.x + material.specularF90 * dfgV.y;
	vec3 FssEss_L = material.specularColorBlended * dfgL.x + material.specularF90 * dfgL.y;
	float Ess_V = dfgV.x + dfgV.y;
	float Ess_L = dfgL.x + dfgL.y;
	float Ems_V = 1.0 - Ess_V;
	float Ems_L = 1.0 - Ess_L;
	vec3 Favg = material.specularColorBlended + ( 1.0 - material.specularColorBlended ) * 0.047619;
	vec3 Fms = FssEss_V * FssEss_L * Favg / ( 1.0 - Ems_V * Ems_L * Favg + EPSILON );
	float compensationFactor = Ems_V * Ems_L;
	vec3 multiScatter = Fms * compensationFactor;
	return singleScatter + multiScatter;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColorBlended * t2.x + ( material.specularF90 - material.specularColorBlended ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseContribution * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
		#ifdef USE_CLEARCOAT
			vec3 Ncc = geometryClearcoatNormal;
			vec2 uvClearcoat = LTC_Uv( Ncc, viewDir, material.clearcoatRoughness );
			vec4 t1Clearcoat = texture2D( ltc_1, uvClearcoat );
			vec4 t2Clearcoat = texture2D( ltc_2, uvClearcoat );
			mat3 mInvClearcoat = mat3(
				vec3( t1Clearcoat.x, 0, t1Clearcoat.y ),
				vec3(             0, 1,             0 ),
				vec3( t1Clearcoat.z, 0, t1Clearcoat.w )
			);
			vec3 fresnelClearcoat = material.clearcoatF0 * t2Clearcoat.x + ( material.clearcoatF90 - material.clearcoatF0 ) * t2Clearcoat.y;
			clearcoatSpecularDirect += lightColor * fresnelClearcoat * LTC_Evaluate( Ncc, viewDir, position, mInvClearcoat, rectCoords );
		#endif
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
 
 		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
 
 		float sheenAlbedoV = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
 		float sheenAlbedoL = IBLSheenBRDF( geometryNormal, directLight.direction, material.sheenRoughness );
 
 		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * max( sheenAlbedoV, sheenAlbedoL );
 
 		irradiance *= sheenEnergyComp;
 
 	#endif
	reflectedLight.directSpecular += irradiance * BRDF_GGX_Multiscatter( directLight.direction, geometryViewDir, geometryNormal, material );
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseContribution );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 diffuse = irradiance * BRDF_Lambert( material.diffuseContribution );
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		diffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectDiffuse += diffuse;
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness ) * RECIPROCAL_PI;
 	#endif
	vec3 singleScatteringDielectric = vec3( 0.0 );
	vec3 multiScatteringDielectric = vec3( 0.0 );
	vec3 singleScatteringMetallic = vec3( 0.0 );
	vec3 multiScatteringMetallic = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.iridescence, material.iridescenceFresnelDielectric, material.roughness, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.diffuseColor, material.specularF90, material.iridescence, material.iridescenceFresnelMetallic, material.roughness, singleScatteringMetallic, multiScatteringMetallic );
	#else
		computeMultiscattering( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.roughness, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscattering( geometryNormal, geometryViewDir, material.diffuseColor, material.specularF90, material.roughness, singleScatteringMetallic, multiScatteringMetallic );
	#endif
	vec3 singleScattering = mix( singleScatteringDielectric, singleScatteringMetallic, material.metalness );
	vec3 multiScattering = mix( multiScatteringDielectric, multiScatteringMetallic, material.metalness );
	vec3 totalScatteringDielectric = singleScatteringDielectric + multiScatteringDielectric;
	vec3 diffuse = material.diffuseContribution * ( 1.0 - totalScatteringDielectric );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	vec3 indirectSpecular = radiance * singleScattering;
	indirectSpecular += multiScattering * cosineWeightedIrradiance;
	vec3 indirectDiffuse = diffuse * cosineWeightedIrradiance;
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		indirectSpecular *= sheenEnergyComp;
		indirectDiffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectSpecular += indirectSpecular;
	reflectedLight.indirectDiffuse += indirectDiffuse;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,pA=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		material.iridescenceFresnelDielectric = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		material.iridescenceFresnelMetallic = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.diffuseColor );
		material.iridescenceFresnel = mix( material.iridescenceFresnelDielectric, material.iridescenceFresnelMetallic, material.metalness );
		material.iridescenceF0 = Schlick_to_F0( material.iridescenceFresnel, 1.0, dotNVi );
	}
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS ) && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,mA=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( ENVMAP_TYPE_CUBE_UV )
		#if defined( STANDARD ) || defined( LAMBERT ) || defined( PHONG )
			iblIrradiance += getIBLIrradiance( geometryNormal );
		#endif
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		radiance += getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		radiance += getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,gA=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,_A=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,vA=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,xA=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,yA=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,SA=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,MA=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,EA=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,bA=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,TA=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,AA=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,RA=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,CA=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,wA=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,DA=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,NA=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,UA=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,LA=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,OA=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,PA=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,FA=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`,IA=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,zA=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,BA=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,HA=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,GA=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,VA=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,kA=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	#ifdef USE_REVERSED_DEPTH_BUFFER
	
		return depth * ( far - near ) - far;
	#else
		return depth * ( near - far ) - near;
	#endif
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	
	#ifdef USE_REVERSED_DEPTH_BUFFER
		return ( near * far ) / ( ( near - far ) * depth - near );
	#else
		return ( near * far ) / ( ( far - near ) * depth - far );
	#endif
}`,jA=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,XA=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,WA=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,qA=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,YA=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,ZA=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,KA=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#else
			uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#endif
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#else
			uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#endif
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform samplerCubeShadow pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#elif defined( SHADOWMAP_TYPE_BASIC )
			uniform samplerCube pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#endif
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float interleavedGradientNoise( vec2 position ) {
			return fract( 52.9829189 * fract( dot( position, vec2( 0.06711056, 0.00583715 ) ) ) );
		}
		vec2 vogelDiskSample( int sampleIndex, int samplesCount, float phi ) {
			const float goldenAngle = 2.399963229728653;
			float r = sqrt( ( float( sampleIndex ) + 0.5 ) / float( samplesCount ) );
			float theta = float( sampleIndex ) * goldenAngle + phi;
			return vec2( cos( theta ), sin( theta ) ) * r;
		}
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float getShadow( sampler2DShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			shadowCoord.z += shadowBias;
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
				float radius = shadowRadius * texelSize.x;
				float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
				shadow = (
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 0, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 1, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 2, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 3, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 4, 5, phi ) * radius, shadowCoord.z ) )
				) * 0.2;
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#elif defined( SHADOWMAP_TYPE_VSM )
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 distribution = texture2D( shadowMap, shadowCoord.xy ).rg;
				float mean = distribution.x;
				float variance = distribution.y * distribution.y;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					float hard_shadow = step( mean, shadowCoord.z );
				#else
					float hard_shadow = step( shadowCoord.z, mean );
				#endif
				
				if ( hard_shadow == 1.0 ) {
					shadow = 1.0;
				} else {
					variance = max( variance, 0.0000001 );
					float d = shadowCoord.z - mean;
					float p_max = variance / ( variance + d * d );
					p_max = clamp( ( p_max - 0.3 ) / 0.65, 0.0, 1.0 );
					shadow = max( hard_shadow, p_max );
				}
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#else
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				float depth = texture2D( shadowMap, shadowCoord.xy ).r;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					shadow = step( depth, shadowCoord.z );
				#else
					shadow = step( shadowCoord.z, depth );
				#endif
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	#if defined( SHADOWMAP_TYPE_PCF )
	float getPointShadow( samplerCubeShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 bd3D = normalize( lightToPosition );
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			#ifdef USE_REVERSED_DEPTH_BUFFER
				float dp = ( shadowCameraNear * ( shadowCameraFar - viewSpaceZ ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp -= shadowBias;
			#else
				float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp += shadowBias;
			#endif
			float texelSize = shadowRadius / shadowMapSize.x;
			vec3 absDir = abs( bd3D );
			vec3 tangent = absDir.x > absDir.z ? vec3( 0.0, 1.0, 0.0 ) : vec3( 1.0, 0.0, 0.0 );
			tangent = normalize( cross( bd3D, tangent ) );
			vec3 bitangent = cross( bd3D, tangent );
			float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
			vec2 sample0 = vogelDiskSample( 0, 5, phi );
			vec2 sample1 = vogelDiskSample( 1, 5, phi );
			vec2 sample2 = vogelDiskSample( 2, 5, phi );
			vec2 sample3 = vogelDiskSample( 3, 5, phi );
			vec2 sample4 = vogelDiskSample( 4, 5, phi );
			shadow = (
				texture( shadowMap, vec4( bd3D + ( tangent * sample0.x + bitangent * sample0.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample1.x + bitangent * sample1.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample2.x + bitangent * sample2.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample3.x + bitangent * sample3.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample4.x + bitangent * sample4.y ) * texelSize, dp ) )
			) * 0.2;
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#elif defined( SHADOWMAP_TYPE_BASIC )
	float getPointShadow( samplerCube shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			float depth = textureCube( shadowMap, bd3D ).r;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				depth = 1.0 - depth;
			#endif
			shadow = step( dp, depth );
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#endif
	#endif
#endif`,QA=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,JA=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	vec3 shadowWorldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,$A=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0 && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,e1=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,t1=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,n1=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,i1=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,a1=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,s1=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,r1=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,o1=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,l1=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = inverseTransformDirection( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseContribution, material.specularColorBlended, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,c1=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,u1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,f1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,h1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,d1=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`;const p1=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,m1=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,g1=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,_1=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float flipEnvMap;
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vec3( flipEnvMap * vWorldDirection.x, vWorldDirection.yz ) );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,v1=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,x1=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,y1=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,S1=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSED_DEPTH_BUFFER
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,M1=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,E1=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main () {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = vec4( dist, 0.0, 0.0, 1.0 );
}`,b1=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,T1=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,A1=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,R1=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,C1=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,w1=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,D1=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,N1=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,U1=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,L1=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,O1=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,P1=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( normalize( normal ) * 0.5 + 0.5, diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,F1=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,I1=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,z1=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,B1=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
 
		outgoingLight = outgoingLight + sheenSpecularDirect + sheenSpecularIndirect;
 
 	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,H1=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,G1=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,V1=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,k1=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,j1=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,X1=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,W1=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,q1=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,pt={alphahash_fragment:mT,alphahash_pars_fragment:gT,alphamap_fragment:_T,alphamap_pars_fragment:vT,alphatest_fragment:xT,alphatest_pars_fragment:yT,aomap_fragment:ST,aomap_pars_fragment:MT,batching_pars_vertex:ET,batching_vertex:bT,begin_vertex:TT,beginnormal_vertex:AT,bsdfs:RT,iridescence_fragment:CT,bumpmap_pars_fragment:wT,clipping_planes_fragment:DT,clipping_planes_pars_fragment:NT,clipping_planes_pars_vertex:UT,clipping_planes_vertex:LT,color_fragment:OT,color_pars_fragment:PT,color_pars_vertex:FT,color_vertex:IT,common:zT,cube_uv_reflection_fragment:BT,defaultnormal_vertex:HT,displacementmap_pars_vertex:GT,displacementmap_vertex:VT,emissivemap_fragment:kT,emissivemap_pars_fragment:jT,colorspace_fragment:XT,colorspace_pars_fragment:WT,envmap_fragment:qT,envmap_common_pars_fragment:YT,envmap_pars_fragment:ZT,envmap_pars_vertex:KT,envmap_physical_pars_fragment:oA,envmap_vertex:QT,fog_vertex:JT,fog_pars_vertex:$T,fog_fragment:eA,fog_pars_fragment:tA,gradientmap_pars_fragment:nA,lightmap_pars_fragment:iA,lights_lambert_fragment:aA,lights_lambert_pars_fragment:sA,lights_pars_begin:rA,lights_toon_fragment:lA,lights_toon_pars_fragment:cA,lights_phong_fragment:uA,lights_phong_pars_fragment:fA,lights_physical_fragment:hA,lights_physical_pars_fragment:dA,lights_fragment_begin:pA,lights_fragment_maps:mA,lights_fragment_end:gA,logdepthbuf_fragment:_A,logdepthbuf_pars_fragment:vA,logdepthbuf_pars_vertex:xA,logdepthbuf_vertex:yA,map_fragment:SA,map_pars_fragment:MA,map_particle_fragment:EA,map_particle_pars_fragment:bA,metalnessmap_fragment:TA,metalnessmap_pars_fragment:AA,morphinstance_vertex:RA,morphcolor_vertex:CA,morphnormal_vertex:wA,morphtarget_pars_vertex:DA,morphtarget_vertex:NA,normal_fragment_begin:UA,normal_fragment_maps:LA,normal_pars_fragment:OA,normal_pars_vertex:PA,normal_vertex:FA,normalmap_pars_fragment:IA,clearcoat_normal_fragment_begin:zA,clearcoat_normal_fragment_maps:BA,clearcoat_pars_fragment:HA,iridescence_pars_fragment:GA,opaque_fragment:VA,packing:kA,premultiplied_alpha_fragment:jA,project_vertex:XA,dithering_fragment:WA,dithering_pars_fragment:qA,roughnessmap_fragment:YA,roughnessmap_pars_fragment:ZA,shadowmap_pars_fragment:KA,shadowmap_pars_vertex:QA,shadowmap_vertex:JA,shadowmask_pars_fragment:$A,skinbase_vertex:e1,skinning_pars_vertex:t1,skinning_vertex:n1,skinnormal_vertex:i1,specularmap_fragment:a1,specularmap_pars_fragment:s1,tonemapping_fragment:r1,tonemapping_pars_fragment:o1,transmission_fragment:l1,transmission_pars_fragment:c1,uv_pars_fragment:u1,uv_pars_vertex:f1,uv_vertex:h1,worldpos_vertex:d1,background_vert:p1,background_frag:m1,backgroundCube_vert:g1,backgroundCube_frag:_1,cube_vert:v1,cube_frag:x1,depth_vert:y1,depth_frag:S1,distance_vert:M1,distance_frag:E1,equirect_vert:b1,equirect_frag:T1,linedashed_vert:A1,linedashed_frag:R1,meshbasic_vert:C1,meshbasic_frag:w1,meshlambert_vert:D1,meshlambert_frag:N1,meshmatcap_vert:U1,meshmatcap_frag:L1,meshnormal_vert:O1,meshnormal_frag:P1,meshphong_vert:F1,meshphong_frag:I1,meshphysical_vert:z1,meshphysical_frag:B1,meshtoon_vert:H1,meshtoon_frag:G1,points_vert:V1,points_frag:k1,shadow_vert:j1,shadow_frag:X1,sprite_vert:W1,sprite_frag:q1},Oe={common:{diffuse:{value:new Lt(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new dt},alphaMap:{value:null},alphaMapTransform:{value:new dt},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new dt}},envmap:{envMap:{value:null},envMapRotation:{value:new dt},flipEnvMap:{value:-1},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new dt}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new dt}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new dt},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new dt},normalScale:{value:new mt(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new dt},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new dt}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new dt}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new dt}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new Lt(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null}},points:{diffuse:{value:new Lt(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new dt},alphaTest:{value:0},uvTransform:{value:new dt}},sprite:{diffuse:{value:new Lt(16777215)},opacity:{value:1},center:{value:new mt(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new dt},alphaMap:{value:null},alphaMapTransform:{value:new dt},alphaTest:{value:0}}},ji={basic:{uniforms:zn([Oe.common,Oe.specularmap,Oe.envmap,Oe.aomap,Oe.lightmap,Oe.fog]),vertexShader:pt.meshbasic_vert,fragmentShader:pt.meshbasic_frag},lambert:{uniforms:zn([Oe.common,Oe.specularmap,Oe.envmap,Oe.aomap,Oe.lightmap,Oe.emissivemap,Oe.bumpmap,Oe.normalmap,Oe.displacementmap,Oe.fog,Oe.lights,{emissive:{value:new Lt(0)},envMapIntensity:{value:1}}]),vertexShader:pt.meshlambert_vert,fragmentShader:pt.meshlambert_frag},phong:{uniforms:zn([Oe.common,Oe.specularmap,Oe.envmap,Oe.aomap,Oe.lightmap,Oe.emissivemap,Oe.bumpmap,Oe.normalmap,Oe.displacementmap,Oe.fog,Oe.lights,{emissive:{value:new Lt(0)},specular:{value:new Lt(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:pt.meshphong_vert,fragmentShader:pt.meshphong_frag},standard:{uniforms:zn([Oe.common,Oe.envmap,Oe.aomap,Oe.lightmap,Oe.emissivemap,Oe.bumpmap,Oe.normalmap,Oe.displacementmap,Oe.roughnessmap,Oe.metalnessmap,Oe.fog,Oe.lights,{emissive:{value:new Lt(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:pt.meshphysical_vert,fragmentShader:pt.meshphysical_frag},toon:{uniforms:zn([Oe.common,Oe.aomap,Oe.lightmap,Oe.emissivemap,Oe.bumpmap,Oe.normalmap,Oe.displacementmap,Oe.gradientmap,Oe.fog,Oe.lights,{emissive:{value:new Lt(0)}}]),vertexShader:pt.meshtoon_vert,fragmentShader:pt.meshtoon_frag},matcap:{uniforms:zn([Oe.common,Oe.bumpmap,Oe.normalmap,Oe.displacementmap,Oe.fog,{matcap:{value:null}}]),vertexShader:pt.meshmatcap_vert,fragmentShader:pt.meshmatcap_frag},points:{uniforms:zn([Oe.points,Oe.fog]),vertexShader:pt.points_vert,fragmentShader:pt.points_frag},dashed:{uniforms:zn([Oe.common,Oe.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:pt.linedashed_vert,fragmentShader:pt.linedashed_frag},depth:{uniforms:zn([Oe.common,Oe.displacementmap]),vertexShader:pt.depth_vert,fragmentShader:pt.depth_frag},normal:{uniforms:zn([Oe.common,Oe.bumpmap,Oe.normalmap,Oe.displacementmap,{opacity:{value:1}}]),vertexShader:pt.meshnormal_vert,fragmentShader:pt.meshnormal_frag},sprite:{uniforms:zn([Oe.sprite,Oe.fog]),vertexShader:pt.sprite_vert,fragmentShader:pt.sprite_frag},background:{uniforms:{uvTransform:{value:new dt},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:pt.background_vert,fragmentShader:pt.background_frag},backgroundCube:{uniforms:{envMap:{value:null},flipEnvMap:{value:-1},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new dt}},vertexShader:pt.backgroundCube_vert,fragmentShader:pt.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:pt.cube_vert,fragmentShader:pt.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:pt.equirect_vert,fragmentShader:pt.equirect_frag},distance:{uniforms:zn([Oe.common,Oe.displacementmap,{referencePosition:{value:new se},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:pt.distance_vert,fragmentShader:pt.distance_frag},shadow:{uniforms:zn([Oe.lights,Oe.fog,{color:{value:new Lt(0)},opacity:{value:1}}]),vertexShader:pt.shadow_vert,fragmentShader:pt.shadow_frag}};ji.physical={uniforms:zn([ji.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new dt},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new dt},clearcoatNormalScale:{value:new mt(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new dt},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new dt},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new dt},sheen:{value:0},sheenColor:{value:new Lt(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new dt},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new dt},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new dt},transmissionSamplerSize:{value:new mt},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new dt},attenuationDistance:{value:0},attenuationColor:{value:new Lt(0)},specularColor:{value:new Lt(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new dt},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new dt},anisotropyVector:{value:new mt},anisotropyMap:{value:null},anisotropyMapTransform:{value:new dt}}]),vertexShader:pt.meshphysical_vert,fragmentShader:pt.meshphysical_frag};const $c={r:0,b:0,g:0},zs=new Da,Y1=new nn;function Z1(s,e,i,r,l,c){const f=new Lt(0);let p=l===!0?0:1,m,d,_=null,v=0,g=null;function M(T){let U=T.isScene===!0?T.background:null;if(U&&U.isTexture){const P=T.backgroundBlurriness>0;U=e.get(U,P)}return U}function E(T){let U=!1;const P=M(T);P===null?x(f,p):P&&P.isColor&&(x(P,1),U=!0);const V=s.xr.getEnvironmentBlendMode();V==="additive"?i.buffers.color.setClear(0,0,0,1,c):V==="alpha-blend"&&i.buffers.color.setClear(0,0,0,0,c),(s.autoClear||U)&&(i.buffers.depth.setTest(!0),i.buffers.depth.setMask(!0),i.buffers.color.setMask(!0),s.clear(s.autoClearColor,s.autoClearDepth,s.autoClearStencil))}function R(T,U){const P=M(U);P&&(P.isCubeTexture||P.mapping===vu)?(d===void 0&&(d=new Na(new ml(1,1,1),new Ki({name:"BackgroundCubeMaterial",uniforms:Kr(ji.backgroundCube.uniforms),vertexShader:ji.backgroundCube.vertexShader,fragmentShader:ji.backgroundCube.fragmentShader,side:Zn,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),d.geometry.deleteAttribute("normal"),d.geometry.deleteAttribute("uv"),d.onBeforeRender=function(V,H,z){this.matrixWorld.copyPosition(z.matrixWorld)},Object.defineProperty(d.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),r.update(d)),zs.copy(U.backgroundRotation),zs.x*=-1,zs.y*=-1,zs.z*=-1,P.isCubeTexture&&P.isRenderTargetTexture===!1&&(zs.y*=-1,zs.z*=-1),d.material.uniforms.envMap.value=P,d.material.uniforms.flipEnvMap.value=P.isCubeTexture&&P.isRenderTargetTexture===!1?-1:1,d.material.uniforms.backgroundBlurriness.value=U.backgroundBlurriness,d.material.uniforms.backgroundIntensity.value=U.backgroundIntensity,d.material.uniforms.backgroundRotation.value.setFromMatrix4(Y1.makeRotationFromEuler(zs)),d.material.toneMapped=Rt.getTransfer(P.colorSpace)!==Bt,(_!==P||v!==P.version||g!==s.toneMapping)&&(d.material.needsUpdate=!0,_=P,v=P.version,g=s.toneMapping),d.layers.enableAll(),T.unshift(d,d.geometry,d.material,0,0,null)):P&&P.isTexture&&(m===void 0&&(m=new Na(new Su(2,2),new Ki({name:"BackgroundMaterial",uniforms:Kr(ji.background.uniforms),vertexShader:ji.background.vertexShader,fragmentShader:ji.background.fragmentShader,side:ds,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),m.geometry.deleteAttribute("normal"),Object.defineProperty(m.material,"map",{get:function(){return this.uniforms.t2D.value}}),r.update(m)),m.material.uniforms.t2D.value=P,m.material.uniforms.backgroundIntensity.value=U.backgroundIntensity,m.material.toneMapped=Rt.getTransfer(P.colorSpace)!==Bt,P.matrixAutoUpdate===!0&&P.updateMatrix(),m.material.uniforms.uvTransform.value.copy(P.matrix),(_!==P||v!==P.version||g!==s.toneMapping)&&(m.material.needsUpdate=!0,_=P,v=P.version,g=s.toneMapping),m.layers.enableAll(),T.unshift(m,m.geometry,m.material,0,0,null))}function x(T,U){T.getRGB($c,bx(s)),i.buffers.color.setClear($c.r,$c.g,$c.b,U,c)}function y(){d!==void 0&&(d.geometry.dispose(),d.material.dispose(),d=void 0),m!==void 0&&(m.geometry.dispose(),m.material.dispose(),m=void 0)}return{getClearColor:function(){return f},setClearColor:function(T,U=1){f.set(T),p=U,x(f,p)},getClearAlpha:function(){return p},setClearAlpha:function(T){p=T,x(f,p)},render:E,addToRenderList:R,dispose:y}}function K1(s,e){const i=s.getParameter(s.MAX_VERTEX_ATTRIBS),r={},l=g(null);let c=l,f=!1;function p(w,Y,re,fe,ee){let I=!1;const B=v(w,fe,re,Y);c!==B&&(c=B,d(c.object)),I=M(w,fe,re,ee),I&&E(w,fe,re,ee),ee!==null&&e.update(ee,s.ELEMENT_ARRAY_BUFFER),(I||f)&&(f=!1,P(w,Y,re,fe),ee!==null&&s.bindBuffer(s.ELEMENT_ARRAY_BUFFER,e.get(ee).buffer))}function m(){return s.createVertexArray()}function d(w){return s.bindVertexArray(w)}function _(w){return s.deleteVertexArray(w)}function v(w,Y,re,fe){const ee=fe.wireframe===!0;let I=r[Y.id];I===void 0&&(I={},r[Y.id]=I);const B=w.isInstancedMesh===!0?w.id:0;let $=I[B];$===void 0&&($={},I[B]=$);let Q=$[re.id];Q===void 0&&(Q={},$[re.id]=Q);let de=Q[ee];return de===void 0&&(de=g(m()),Q[ee]=de),de}function g(w){const Y=[],re=[],fe=[];for(let ee=0;ee<i;ee++)Y[ee]=0,re[ee]=0,fe[ee]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:Y,enabledAttributes:re,attributeDivisors:fe,object:w,attributes:{},index:null}}function M(w,Y,re,fe){const ee=c.attributes,I=Y.attributes;let B=0;const $=re.getAttributes();for(const Q in $)if($[Q].location>=0){const O=ee[Q];let j=I[Q];if(j===void 0&&(Q==="instanceMatrix"&&w.instanceMatrix&&(j=w.instanceMatrix),Q==="instanceColor"&&w.instanceColor&&(j=w.instanceColor)),O===void 0||O.attribute!==j||j&&O.data!==j.data)return!0;B++}return c.attributesNum!==B||c.index!==fe}function E(w,Y,re,fe){const ee={},I=Y.attributes;let B=0;const $=re.getAttributes();for(const Q in $)if($[Q].location>=0){let O=I[Q];O===void 0&&(Q==="instanceMatrix"&&w.instanceMatrix&&(O=w.instanceMatrix),Q==="instanceColor"&&w.instanceColor&&(O=w.instanceColor));const j={};j.attribute=O,O&&O.data&&(j.data=O.data),ee[Q]=j,B++}c.attributes=ee,c.attributesNum=B,c.index=fe}function R(){const w=c.newAttributes;for(let Y=0,re=w.length;Y<re;Y++)w[Y]=0}function x(w){y(w,0)}function y(w,Y){const re=c.newAttributes,fe=c.enabledAttributes,ee=c.attributeDivisors;re[w]=1,fe[w]===0&&(s.enableVertexAttribArray(w),fe[w]=1),ee[w]!==Y&&(s.vertexAttribDivisor(w,Y),ee[w]=Y)}function T(){const w=c.newAttributes,Y=c.enabledAttributes;for(let re=0,fe=Y.length;re<fe;re++)Y[re]!==w[re]&&(s.disableVertexAttribArray(re),Y[re]=0)}function U(w,Y,re,fe,ee,I,B){B===!0?s.vertexAttribIPointer(w,Y,re,ee,I):s.vertexAttribPointer(w,Y,re,fe,ee,I)}function P(w,Y,re,fe){R();const ee=fe.attributes,I=re.getAttributes(),B=Y.defaultAttributeValues;for(const $ in I){const Q=I[$];if(Q.location>=0){let de=ee[$];if(de===void 0&&($==="instanceMatrix"&&w.instanceMatrix&&(de=w.instanceMatrix),$==="instanceColor"&&w.instanceColor&&(de=w.instanceColor)),de!==void 0){const O=de.normalized,j=de.itemSize,ve=e.get(de);if(ve===void 0)continue;const he=ve.buffer,Ne=ve.type,ie=ve.bytesPerElement,Se=Ne===s.INT||Ne===s.UNSIGNED_INT||de.gpuType===Mp;if(de.isInterleavedBufferAttribute){const Ae=de.data,Ge=Ae.stride,Qe=de.offset;if(Ae.isInstancedInterleavedBuffer){for(let qe=0;qe<Q.locationSize;qe++)y(Q.location+qe,Ae.meshPerAttribute);w.isInstancedMesh!==!0&&fe._maxInstanceCount===void 0&&(fe._maxInstanceCount=Ae.meshPerAttribute*Ae.count)}else for(let qe=0;qe<Q.locationSize;qe++)x(Q.location+qe);s.bindBuffer(s.ARRAY_BUFFER,he);for(let qe=0;qe<Q.locationSize;qe++)U(Q.location+qe,j/Q.locationSize,Ne,O,Ge*ie,(Qe+j/Q.locationSize*qe)*ie,Se)}else{if(de.isInstancedBufferAttribute){for(let Ae=0;Ae<Q.locationSize;Ae++)y(Q.location+Ae,de.meshPerAttribute);w.isInstancedMesh!==!0&&fe._maxInstanceCount===void 0&&(fe._maxInstanceCount=de.meshPerAttribute*de.count)}else for(let Ae=0;Ae<Q.locationSize;Ae++)x(Q.location+Ae);s.bindBuffer(s.ARRAY_BUFFER,he);for(let Ae=0;Ae<Q.locationSize;Ae++)U(Q.location+Ae,j/Q.locationSize,Ne,O,j*ie,j/Q.locationSize*Ae*ie,Se)}}else if(B!==void 0){const O=B[$];if(O!==void 0)switch(O.length){case 2:s.vertexAttrib2fv(Q.location,O);break;case 3:s.vertexAttrib3fv(Q.location,O);break;case 4:s.vertexAttrib4fv(Q.location,O);break;default:s.vertexAttrib1fv(Q.location,O)}}}}T()}function V(){L();for(const w in r){const Y=r[w];for(const re in Y){const fe=Y[re];for(const ee in fe){const I=fe[ee];for(const B in I)_(I[B].object),delete I[B];delete fe[ee]}}delete r[w]}}function H(w){if(r[w.id]===void 0)return;const Y=r[w.id];for(const re in Y){const fe=Y[re];for(const ee in fe){const I=fe[ee];for(const B in I)_(I[B].object),delete I[B];delete fe[ee]}}delete r[w.id]}function z(w){for(const Y in r){const re=r[Y];for(const fe in re){const ee=re[fe];if(ee[w.id]===void 0)continue;const I=ee[w.id];for(const B in I)_(I[B].object),delete I[B];delete ee[w.id]}}}function A(w){for(const Y in r){const re=r[Y],fe=w.isInstancedMesh===!0?w.id:0,ee=re[fe];if(ee!==void 0){for(const I in ee){const B=ee[I];for(const $ in B)_(B[$].object),delete B[$];delete ee[I]}delete re[fe],Object.keys(re).length===0&&delete r[Y]}}}function L(){pe(),f=!0,c!==l&&(c=l,d(c.object))}function pe(){l.geometry=null,l.program=null,l.wireframe=!1}return{setup:p,reset:L,resetDefaultState:pe,dispose:V,releaseStatesOfGeometry:H,releaseStatesOfObject:A,releaseStatesOfProgram:z,initAttributes:R,enableAttribute:x,disableUnusedAttributes:T}}function Q1(s,e,i){let r;function l(d){r=d}function c(d,_){s.drawArrays(r,d,_),i.update(_,r,1)}function f(d,_,v){v!==0&&(s.drawArraysInstanced(r,d,_,v),i.update(_,r,v))}function p(d,_,v){if(v===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(r,d,0,_,0,v);let M=0;for(let E=0;E<v;E++)M+=_[E];i.update(M,r,1)}function m(d,_,v,g){if(v===0)return;const M=e.get("WEBGL_multi_draw");if(M===null)for(let E=0;E<d.length;E++)f(d[E],_[E],g[E]);else{M.multiDrawArraysInstancedWEBGL(r,d,0,_,0,g,0,v);let E=0;for(let R=0;R<v;R++)E+=_[R]*g[R];i.update(E,r,1)}}this.setMode=l,this.render=c,this.renderInstances=f,this.renderMultiDraw=p,this.renderMultiDrawInstances=m}function J1(s,e,i,r){let l;function c(){if(l!==void 0)return l;if(e.has("EXT_texture_filter_anisotropic")===!0){const z=e.get("EXT_texture_filter_anisotropic");l=s.getParameter(z.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else l=0;return l}function f(z){return!(z!==Li&&r.convert(z)!==s.getParameter(s.IMPLEMENTATION_COLOR_READ_FORMAT))}function p(z){const A=z===Ca&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(z!==Si&&r.convert(z)!==s.getParameter(s.IMPLEMENTATION_COLOR_READ_TYPE)&&z!==Xi&&!A)}function m(z){if(z==="highp"){if(s.getShaderPrecisionFormat(s.VERTEX_SHADER,s.HIGH_FLOAT).precision>0&&s.getShaderPrecisionFormat(s.FRAGMENT_SHADER,s.HIGH_FLOAT).precision>0)return"highp";z="mediump"}return z==="mediump"&&s.getShaderPrecisionFormat(s.VERTEX_SHADER,s.MEDIUM_FLOAT).precision>0&&s.getShaderPrecisionFormat(s.FRAGMENT_SHADER,s.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let d=i.precision!==void 0?i.precision:"highp";const _=m(d);_!==d&&(st("WebGLRenderer:",d,"not supported, using",_,"instead."),d=_);const v=i.logarithmicDepthBuffer===!0,g=i.reversedDepthBuffer===!0&&e.has("EXT_clip_control"),M=s.getParameter(s.MAX_TEXTURE_IMAGE_UNITS),E=s.getParameter(s.MAX_VERTEX_TEXTURE_IMAGE_UNITS),R=s.getParameter(s.MAX_TEXTURE_SIZE),x=s.getParameter(s.MAX_CUBE_MAP_TEXTURE_SIZE),y=s.getParameter(s.MAX_VERTEX_ATTRIBS),T=s.getParameter(s.MAX_VERTEX_UNIFORM_VECTORS),U=s.getParameter(s.MAX_VARYING_VECTORS),P=s.getParameter(s.MAX_FRAGMENT_UNIFORM_VECTORS),V=s.getParameter(s.MAX_SAMPLES),H=s.getParameter(s.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:c,getMaxPrecision:m,textureFormatReadable:f,textureTypeReadable:p,precision:d,logarithmicDepthBuffer:v,reversedDepthBuffer:g,maxTextures:M,maxVertexTextures:E,maxTextureSize:R,maxCubemapSize:x,maxAttributes:y,maxVertexUniforms:T,maxVaryings:U,maxFragmentUniforms:P,maxSamples:V,samples:H}}function $1(s){const e=this;let i=null,r=0,l=!1,c=!1;const f=new us,p=new dt,m={value:null,needsUpdate:!1};this.uniform=m,this.numPlanes=0,this.numIntersection=0,this.init=function(v,g){const M=v.length!==0||g||r!==0||l;return l=g,r=v.length,M},this.beginShadows=function(){c=!0,_(null)},this.endShadows=function(){c=!1},this.setGlobalState=function(v,g){i=_(v,g,0)},this.setState=function(v,g,M){const E=v.clippingPlanes,R=v.clipIntersection,x=v.clipShadows,y=s.get(v);if(!l||E===null||E.length===0||c&&!x)c?_(null):d();else{const T=c?0:r,U=T*4;let P=y.clippingState||null;m.value=P,P=_(E,g,U,M);for(let V=0;V!==U;++V)P[V]=i[V];y.clippingState=P,this.numIntersection=R?this.numPlanes:0,this.numPlanes+=T}};function d(){m.value!==i&&(m.value=i,m.needsUpdate=r>0),e.numPlanes=r,e.numIntersection=0}function _(v,g,M,E){const R=v!==null?v.length:0;let x=null;if(R!==0){if(x=m.value,E!==!0||x===null){const y=M+R*4,T=g.matrixWorldInverse;p.getNormalMatrix(T),(x===null||x.length<y)&&(x=new Float32Array(y));for(let U=0,P=M;U!==R;++U,P+=4)f.copy(v[U]).applyMatrix4(T,p),f.normal.toArray(x,P),x[P+3]=f.constant}m.value=x,m.needsUpdate=!0}return e.numPlanes=R,e.numIntersection=0,x}}const hs=4,rv=[.125,.215,.35,.446,.526,.582],Gs=20,eR=256,$o=new Ax,ov=new Lt;let cd=null,ud=0,fd=0,hd=!1;const tR=new se;class lv{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._sigmas=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,i=0,r=.1,l=100,c={}){const{size:f=256,position:p=tR}=c;cd=this._renderer.getRenderTarget(),ud=this._renderer.getActiveCubeFace(),fd=this._renderer.getActiveMipmapLevel(),hd=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(f);const m=this._allocateTargets();return m.depthBuffer=!0,this._sceneToCubeUV(e,r,l,m,p),i>0&&this._blur(m,0,0,i),this._applyPMREM(m),this._cleanup(m),m}fromEquirectangular(e,i=null){return this._fromTexture(e,i)}fromCubemap(e,i=null){return this._fromTexture(e,i)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=fv(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=uv(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(cd,ud,fd),this._renderer.xr.enabled=hd,e.scissorTest=!1,Gr(e,0,0,e.width,e.height)}_fromTexture(e,i){e.mapping===js||e.mapping===qr?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),cd=this._renderer.getRenderTarget(),ud=this._renderer.getActiveCubeFace(),fd=this._renderer.getActiveMipmapLevel(),hd=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;const r=i||this._allocateTargets();return this._textureToCubeUV(e,r),this._applyPMREM(r),this._cleanup(r),r}_allocateTargets(){const e=3*Math.max(this._cubeSize,112),i=4*this._cubeSize,r={magFilter:Nn,minFilter:Nn,generateMipmaps:!1,type:Ca,format:Li,colorSpace:Zr,depthBuffer:!1},l=cv(e,i,r);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==i){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=cv(e,i,r);const{_lodMax:c}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods,sigmas:this._sigmas}=nR(c)),this._blurMaterial=aR(c,e,i),this._ggxMaterial=iR(c,e,i)}return l}_compileMaterial(e){const i=new Na(new Fi,e);this._renderer.compile(i,$o)}_sceneToCubeUV(e,i,r,l,c){const m=new yi(90,1,i,r),d=[1,-1,1,1,1,1],_=[1,1,1,-1,-1,-1],v=this._renderer,g=v.autoClear,M=v.toneMapping;v.getClearColor(ov),v.toneMapping=qi,v.autoClear=!1,v.state.buffers.depth.getReversed()&&(v.setRenderTarget(l),v.clearDepth(),v.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new Na(new ml,new xx({name:"PMREM.Background",side:Zn,depthWrite:!1,depthTest:!1})));const R=this._backgroundBox,x=R.material;let y=!1;const T=e.background;T?T.isColor&&(x.color.copy(T),e.background=null,y=!0):(x.color.copy(ov),y=!0);for(let U=0;U<6;U++){const P=U%3;P===0?(m.up.set(0,d[U],0),m.position.set(c.x,c.y,c.z),m.lookAt(c.x+_[U],c.y,c.z)):P===1?(m.up.set(0,0,d[U]),m.position.set(c.x,c.y,c.z),m.lookAt(c.x,c.y+_[U],c.z)):(m.up.set(0,d[U],0),m.position.set(c.x,c.y,c.z),m.lookAt(c.x,c.y,c.z+_[U]));const V=this._cubeSize;Gr(l,P*V,U>2?V:0,V,V),v.setRenderTarget(l),y&&v.render(R,m),v.render(e,m)}v.toneMapping=M,v.autoClear=g,e.background=T}_textureToCubeUV(e,i){const r=this._renderer,l=e.mapping===js||e.mapping===qr;l?(this._cubemapMaterial===null&&(this._cubemapMaterial=fv()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=uv());const c=l?this._cubemapMaterial:this._equirectMaterial,f=this._lodMeshes[0];f.material=c;const p=c.uniforms;p.envMap.value=e;const m=this._cubeSize;Gr(i,0,0,3*m,2*m),r.setRenderTarget(i),r.render(f,$o)}_applyPMREM(e){const i=this._renderer,r=i.autoClear;i.autoClear=!1;const l=this._lodMeshes.length;for(let c=1;c<l;c++)this._applyGGXFilter(e,c-1,c);i.autoClear=r}_applyGGXFilter(e,i,r){const l=this._renderer,c=this._pingPongRenderTarget,f=this._ggxMaterial,p=this._lodMeshes[r];p.material=f;const m=f.uniforms,d=r/(this._lodMeshes.length-1),_=i/(this._lodMeshes.length-1),v=Math.sqrt(d*d-_*_),g=0+d*1.25,M=v*g,{_lodMax:E}=this,R=this._sizeLods[r],x=3*R*(r>E-hs?r-E+hs:0),y=4*(this._cubeSize-R);m.envMap.value=e.texture,m.roughness.value=M,m.mipInt.value=E-i,Gr(c,x,y,3*R,2*R),l.setRenderTarget(c),l.render(p,$o),m.envMap.value=c.texture,m.roughness.value=0,m.mipInt.value=E-r,Gr(e,x,y,3*R,2*R),l.setRenderTarget(e),l.render(p,$o)}_blur(e,i,r,l,c){const f=this._pingPongRenderTarget;this._halfBlur(e,f,i,r,l,"latitudinal",c),this._halfBlur(f,e,r,r,l,"longitudinal",c)}_halfBlur(e,i,r,l,c,f,p){const m=this._renderer,d=this._blurMaterial;f!=="latitudinal"&&f!=="longitudinal"&&At("blur direction must be either latitudinal or longitudinal!");const _=3,v=this._lodMeshes[l];v.material=d;const g=d.uniforms,M=this._sizeLods[r]-1,E=isFinite(c)?Math.PI/(2*M):2*Math.PI/(2*Gs-1),R=c/E,x=isFinite(c)?1+Math.floor(_*R):Gs;x>Gs&&st(`sigmaRadians, ${c}, is too large and will clip, as it requested ${x} samples when the maximum is set to ${Gs}`);const y=[];let T=0;for(let z=0;z<Gs;++z){const A=z/R,L=Math.exp(-A*A/2);y.push(L),z===0?T+=L:z<x&&(T+=2*L)}for(let z=0;z<y.length;z++)y[z]=y[z]/T;g.envMap.value=e.texture,g.samples.value=x,g.weights.value=y,g.latitudinal.value=f==="latitudinal",p&&(g.poleAxis.value=p);const{_lodMax:U}=this;g.dTheta.value=E,g.mipInt.value=U-r;const P=this._sizeLods[l],V=3*P*(l>U-hs?l-U+hs:0),H=4*(this._cubeSize-P);Gr(i,V,H,3*P,2*P),m.setRenderTarget(i),m.render(v,$o)}}function nR(s){const e=[],i=[],r=[];let l=s;const c=s-hs+1+rv.length;for(let f=0;f<c;f++){const p=Math.pow(2,l);e.push(p);let m=1/p;f>s-hs?m=rv[f-s+hs-1]:f===0&&(m=0),i.push(m);const d=1/(p-2),_=-d,v=1+d,g=[_,_,v,_,v,v,_,_,v,v,_,v],M=6,E=6,R=3,x=2,y=1,T=new Float32Array(R*E*M),U=new Float32Array(x*E*M),P=new Float32Array(y*E*M);for(let H=0;H<M;H++){const z=H%3*2/3-1,A=H>2?0:-1,L=[z,A,0,z+2/3,A,0,z+2/3,A+1,0,z,A,0,z+2/3,A+1,0,z,A+1,0];T.set(L,R*E*H),U.set(g,x*E*H);const pe=[H,H,H,H,H,H];P.set(pe,y*E*H)}const V=new Fi;V.setAttribute("position",new Yn(T,R)),V.setAttribute("uv",new Yn(U,x)),V.setAttribute("faceIndex",new Yn(P,y)),r.push(new Na(V,null)),l>hs&&l--}return{lodMeshes:r,sizeLods:e,sigmas:i}}function cv(s,e,i){const r=new Yi(s,e,i);return r.texture.mapping=vu,r.texture.name="PMREM.cubeUv",r.scissorTest=!0,r}function Gr(s,e,i,r,l){s.viewport.set(e,i,r,l),s.scissor.set(e,i,r,l)}function iR(s,e,i){return new Ki({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:eR,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/i,CUBEUV_MAX_MIP:`${s}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:Mu(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float roughness;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359

			// Van der Corput radical inverse
			float radicalInverse_VdC(uint bits) {
				bits = (bits << 16u) | (bits >> 16u);
				bits = ((bits & 0x55555555u) << 1u) | ((bits & 0xAAAAAAAAu) >> 1u);
				bits = ((bits & 0x33333333u) << 2u) | ((bits & 0xCCCCCCCCu) >> 2u);
				bits = ((bits & 0x0F0F0F0Fu) << 4u) | ((bits & 0xF0F0F0F0u) >> 4u);
				bits = ((bits & 0x00FF00FFu) << 8u) | ((bits & 0xFF00FF00u) >> 8u);
				return float(bits) * 2.3283064365386963e-10; // / 0x100000000
			}

			// Hammersley sequence
			vec2 hammersley(uint i, uint N) {
				return vec2(float(i) / float(N), radicalInverse_VdC(i));
			}

			// GGX VNDF importance sampling (Eric Heitz 2018)
			// "Sampling the GGX Distribution of Visible Normals"
			// https://jcgt.org/published/0007/04/01/
			vec3 importanceSampleGGX_VNDF(vec2 Xi, vec3 V, float roughness) {
				float alpha = roughness * roughness;

				// Section 4.1: Orthonormal basis
				vec3 T1 = vec3(1.0, 0.0, 0.0);
				vec3 T2 = cross(V, T1);

				// Section 4.2: Parameterization of projected area
				float r = sqrt(Xi.x);
				float phi = 2.0 * PI * Xi.y;
				float t1 = r * cos(phi);
				float t2 = r * sin(phi);
				float s = 0.5 * (1.0 + V.z);
				t2 = (1.0 - s) * sqrt(1.0 - t1 * t1) + s * t2;

				// Section 4.3: Reprojection onto hemisphere
				vec3 Nh = t1 * T1 + t2 * T2 + sqrt(max(0.0, 1.0 - t1 * t1 - t2 * t2)) * V;

				// Section 3.4: Transform back to ellipsoid configuration
				return normalize(vec3(alpha * Nh.x, alpha * Nh.y, max(0.0, Nh.z)));
			}

			void main() {
				vec3 N = normalize(vOutputDirection);
				vec3 V = N; // Assume view direction equals normal for pre-filtering

				vec3 prefilteredColor = vec3(0.0);
				float totalWeight = 0.0;

				// For very low roughness, just sample the environment directly
				if (roughness < 0.001) {
					gl_FragColor = vec4(bilinearCubeUV(envMap, N, mipInt), 1.0);
					return;
				}

				// Tangent space basis for VNDF sampling
				vec3 up = abs(N.z) < 0.999 ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
				vec3 tangent = normalize(cross(up, N));
				vec3 bitangent = cross(N, tangent);

				for(uint i = 0u; i < uint(GGX_SAMPLES); i++) {
					vec2 Xi = hammersley(i, uint(GGX_SAMPLES));

					// For PMREM, V = N, so in tangent space V is always (0, 0, 1)
					vec3 H_tangent = importanceSampleGGX_VNDF(Xi, vec3(0.0, 0.0, 1.0), roughness);

					// Transform H back to world space
					vec3 H = normalize(tangent * H_tangent.x + bitangent * H_tangent.y + N * H_tangent.z);
					vec3 L = normalize(2.0 * dot(V, H) * H - V);

					float NdotL = max(dot(N, L), 0.0);

					if(NdotL > 0.0) {
						// Sample environment at fixed mip level
						// VNDF importance sampling handles the distribution filtering
						vec3 sampleColor = bilinearCubeUV(envMap, L, mipInt);

						// Weight by NdotL for the split-sum approximation
						// VNDF PDF naturally accounts for the visible microfacet distribution
						prefilteredColor += sampleColor * NdotL;
						totalWeight += NdotL;
					}
				}

				if (totalWeight > 0.0) {
					prefilteredColor = prefilteredColor / totalWeight;
				}

				gl_FragColor = vec4(prefilteredColor, 1.0);
			}
		`,blending:ba,depthTest:!1,depthWrite:!1})}function aR(s,e,i){const r=new Float32Array(Gs),l=new se(0,1,0);return new Ki({name:"SphericalGaussianBlur",defines:{n:Gs,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/i,CUBEUV_MAX_MIP:`${s}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:r},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:l}},vertexShader:Mu(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform int samples;
			uniform float weights[ n ];
			uniform bool latitudinal;
			uniform float dTheta;
			uniform float mipInt;
			uniform vec3 poleAxis;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			vec3 getSample( float theta, vec3 axis ) {

				float cosTheta = cos( theta );
				// Rodrigues' axis-angle rotation
				vec3 sampleDirection = vOutputDirection * cosTheta
					+ cross( axis, vOutputDirection ) * sin( theta )
					+ axis * dot( axis, vOutputDirection ) * ( 1.0 - cosTheta );

				return bilinearCubeUV( envMap, sampleDirection, mipInt );

			}

			void main() {

				vec3 axis = latitudinal ? poleAxis : cross( poleAxis, vOutputDirection );

				if ( all( equal( axis, vec3( 0.0 ) ) ) ) {

					axis = vec3( vOutputDirection.z, 0.0, - vOutputDirection.x );

				}

				axis = normalize( axis );

				gl_FragColor = vec4( 0.0, 0.0, 0.0, 1.0 );
				gl_FragColor.rgb += weights[ 0 ] * getSample( 0.0, axis );

				for ( int i = 1; i < n; i++ ) {

					if ( i >= samples ) {

						break;

					}

					float theta = dTheta * float( i );
					gl_FragColor.rgb += weights[ i ] * getSample( -1.0 * theta, axis );
					gl_FragColor.rgb += weights[ i ] * getSample( theta, axis );

				}

			}
		`,blending:ba,depthTest:!1,depthWrite:!1})}function uv(){return new Ki({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:Mu(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:ba,depthTest:!1,depthWrite:!1})}function fv(){return new Ki({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:Mu(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:ba,depthTest:!1,depthWrite:!1})}function Mu(){return`

		precision mediump float;
		precision mediump int;

		attribute float faceIndex;

		varying vec3 vOutputDirection;

		// RH coordinate system; PMREM face-indexing convention
		vec3 getDirection( vec2 uv, float face ) {

			uv = 2.0 * uv - 1.0;

			vec3 direction = vec3( uv, 1.0 );

			if ( face == 0.0 ) {

				direction = direction.zyx; // ( 1, v, u ) pos x

			} else if ( face == 1.0 ) {

				direction = direction.xzy;
				direction.xz *= -1.0; // ( -u, 1, -v ) pos y

			} else if ( face == 2.0 ) {

				direction.x *= -1.0; // ( -u, v, 1 ) pos z

			} else if ( face == 3.0 ) {

				direction = direction.zyx;
				direction.xz *= -1.0; // ( -1, v, -u ) neg x

			} else if ( face == 4.0 ) {

				direction = direction.xzy;
				direction.xy *= -1.0; // ( -u, -1, v ) neg y

			} else if ( face == 5.0 ) {

				direction.z *= -1.0; // ( u, v, -1 ) neg z

			}

			return direction;

		}

		void main() {

			vOutputDirection = getDirection( uv, faceIndex );
			gl_Position = vec4( position, 1.0 );

		}
	`}class Cx extends Yi{constructor(e=1,i={}){super(e,e,i),this.isWebGLCubeRenderTarget=!0;const r={width:e,height:e,depth:1},l=[r,r,r,r,r,r];this.texture=new Mx(l),this._setTextureOptions(i),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,i){this.texture.type=i.type,this.texture.colorSpace=i.colorSpace,this.texture.generateMipmaps=i.generateMipmaps,this.texture.minFilter=i.minFilter,this.texture.magFilter=i.magFilter;const r={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},l=new ml(5,5,5),c=new Ki({name:"CubemapFromEquirect",uniforms:Kr(r.uniforms),vertexShader:r.vertexShader,fragmentShader:r.fragmentShader,side:Zn,blending:ba});c.uniforms.tEquirect.value=i;const f=new Na(l,c),p=i.minFilter;return i.minFilter===Vs&&(i.minFilter=Nn),new cT(1,10,this).update(e,f),i.minFilter=p,f.geometry.dispose(),f.material.dispose(),this}clear(e,i=!0,r=!0,l=!0){const c=e.getRenderTarget();for(let f=0;f<6;f++)e.setRenderTarget(this,f),e.clear(i,r,l);e.setRenderTarget(c)}}function sR(s){let e=new WeakMap,i=new WeakMap,r=null;function l(g,M=!1){return g==null?null:M?f(g):c(g)}function c(g){if(g&&g.isTexture){const M=g.mapping;if(M===Ih||M===zh)if(e.has(g)){const E=e.get(g).texture;return p(E,g.mapping)}else{const E=g.image;if(E&&E.height>0){const R=new Cx(E.height);return R.fromEquirectangularTexture(s,g),e.set(g,R),g.addEventListener("dispose",d),p(R.texture,g.mapping)}else return null}}return g}function f(g){if(g&&g.isTexture){const M=g.mapping,E=M===Ih||M===zh,R=M===js||M===qr;if(E||R){let x=i.get(g);const y=x!==void 0?x.texture.pmremVersion:0;if(g.isRenderTargetTexture&&g.pmremVersion!==y)return r===null&&(r=new lv(s)),x=E?r.fromEquirectangular(g,x):r.fromCubemap(g,x),x.texture.pmremVersion=g.pmremVersion,i.set(g,x),x.texture;if(x!==void 0)return x.texture;{const T=g.image;return E&&T&&T.height>0||R&&T&&m(T)?(r===null&&(r=new lv(s)),x=E?r.fromEquirectangular(g):r.fromCubemap(g),x.texture.pmremVersion=g.pmremVersion,i.set(g,x),g.addEventListener("dispose",_),x.texture):null}}}return g}function p(g,M){return M===Ih?g.mapping=js:M===zh&&(g.mapping=qr),g}function m(g){let M=0;const E=6;for(let R=0;R<E;R++)g[R]!==void 0&&M++;return M===E}function d(g){const M=g.target;M.removeEventListener("dispose",d);const E=e.get(M);E!==void 0&&(e.delete(M),E.dispose())}function _(g){const M=g.target;M.removeEventListener("dispose",_);const E=i.get(M);E!==void 0&&(i.delete(M),E.dispose())}function v(){e=new WeakMap,i=new WeakMap,r!==null&&(r.dispose(),r=null)}return{get:l,dispose:v}}function rR(s){const e={};function i(r){if(e[r]!==void 0)return e[r];const l=s.getExtension(r);return e[r]=l,l}return{has:function(r){return i(r)!==null},init:function(){i("EXT_color_buffer_float"),i("WEBGL_clip_cull_distance"),i("OES_texture_float_linear"),i("EXT_color_buffer_half_float"),i("WEBGL_multisampled_render_to_texture"),i("WEBGL_render_shared_exponent")},get:function(r){const l=i(r);return l===null&&mu("WebGLRenderer: "+r+" extension not supported."),l}}}function oR(s,e,i,r){const l={},c=new WeakMap;function f(v){const g=v.target;g.index!==null&&e.remove(g.index);for(const E in g.attributes)e.remove(g.attributes[E]);g.removeEventListener("dispose",f),delete l[g.id];const M=c.get(g);M&&(e.remove(M),c.delete(g)),r.releaseStatesOfGeometry(g),g.isInstancedBufferGeometry===!0&&delete g._maxInstanceCount,i.memory.geometries--}function p(v,g){return l[g.id]===!0||(g.addEventListener("dispose",f),l[g.id]=!0,i.memory.geometries++),g}function m(v){const g=v.attributes;for(const M in g)e.update(g[M],s.ARRAY_BUFFER)}function d(v){const g=[],M=v.index,E=v.attributes.position;let R=0;if(E===void 0)return;if(M!==null){const T=M.array;R=M.version;for(let U=0,P=T.length;U<P;U+=3){const V=T[U+0],H=T[U+1],z=T[U+2];g.push(V,H,H,z,z,V)}}else{const T=E.array;R=E.version;for(let U=0,P=T.length/3-1;U<P;U+=3){const V=U+0,H=U+1,z=U+2;g.push(V,H,H,z,z,V)}}const x=new(E.count>=65535?vx:_x)(g,1);x.version=R;const y=c.get(v);y&&e.remove(y),c.set(v,x)}function _(v){const g=c.get(v);if(g){const M=v.index;M!==null&&g.version<M.version&&d(v)}else d(v);return c.get(v)}return{get:p,update:m,getWireframeAttribute:_}}function lR(s,e,i){let r;function l(g){r=g}let c,f;function p(g){c=g.type,f=g.bytesPerElement}function m(g,M){s.drawElements(r,M,c,g*f),i.update(M,r,1)}function d(g,M,E){E!==0&&(s.drawElementsInstanced(r,M,c,g*f,E),i.update(M,r,E))}function _(g,M,E){if(E===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(r,M,0,c,g,0,E);let x=0;for(let y=0;y<E;y++)x+=M[y];i.update(x,r,1)}function v(g,M,E,R){if(E===0)return;const x=e.get("WEBGL_multi_draw");if(x===null)for(let y=0;y<g.length;y++)d(g[y]/f,M[y],R[y]);else{x.multiDrawElementsInstancedWEBGL(r,M,0,c,g,0,R,0,E);let y=0;for(let T=0;T<E;T++)y+=M[T]*R[T];i.update(y,r,1)}}this.setMode=l,this.setIndex=p,this.render=m,this.renderInstances=d,this.renderMultiDraw=_,this.renderMultiDrawInstances=v}function cR(s){const e={geometries:0,textures:0},i={frame:0,calls:0,triangles:0,points:0,lines:0};function r(c,f,p){switch(i.calls++,f){case s.TRIANGLES:i.triangles+=p*(c/3);break;case s.LINES:i.lines+=p*(c/2);break;case s.LINE_STRIP:i.lines+=p*(c-1);break;case s.LINE_LOOP:i.lines+=p*c;break;case s.POINTS:i.points+=p*c;break;default:At("WebGLInfo: Unknown draw mode:",f);break}}function l(){i.calls=0,i.triangles=0,i.points=0,i.lines=0}return{memory:e,render:i,programs:null,autoReset:!0,reset:l,update:r}}function uR(s,e,i){const r=new WeakMap,l=new rn;function c(f,p,m){const d=f.morphTargetInfluences,_=p.morphAttributes.position||p.morphAttributes.normal||p.morphAttributes.color,v=_!==void 0?_.length:0;let g=r.get(p);if(g===void 0||g.count!==v){let pe=function(){A.dispose(),r.delete(p),p.removeEventListener("dispose",pe)};var M=pe;g!==void 0&&g.texture.dispose();const E=p.morphAttributes.position!==void 0,R=p.morphAttributes.normal!==void 0,x=p.morphAttributes.color!==void 0,y=p.morphAttributes.position||[],T=p.morphAttributes.normal||[],U=p.morphAttributes.color||[];let P=0;E===!0&&(P=1),R===!0&&(P=2),x===!0&&(P=3);let V=p.attributes.position.count*P,H=1;V>e.maxTextureSize&&(H=Math.ceil(V/e.maxTextureSize),V=e.maxTextureSize);const z=new Float32Array(V*H*4*v),A=new mx(z,V,H,v);A.type=Xi,A.needsUpdate=!0;const L=P*4;for(let w=0;w<v;w++){const Y=y[w],re=T[w],fe=U[w],ee=V*H*4*w;for(let I=0;I<Y.count;I++){const B=I*L;E===!0&&(l.fromBufferAttribute(Y,I),z[ee+B+0]=l.x,z[ee+B+1]=l.y,z[ee+B+2]=l.z,z[ee+B+3]=0),R===!0&&(l.fromBufferAttribute(re,I),z[ee+B+4]=l.x,z[ee+B+5]=l.y,z[ee+B+6]=l.z,z[ee+B+7]=0),x===!0&&(l.fromBufferAttribute(fe,I),z[ee+B+8]=l.x,z[ee+B+9]=l.y,z[ee+B+10]=l.z,z[ee+B+11]=fe.itemSize===4?l.w:1)}}g={count:v,texture:A,size:new mt(V,H)},r.set(p,g),p.addEventListener("dispose",pe)}if(f.isInstancedMesh===!0&&f.morphTexture!==null)m.getUniforms().setValue(s,"morphTexture",f.morphTexture,i);else{let E=0;for(let x=0;x<d.length;x++)E+=d[x];const R=p.morphTargetsRelative?1:1-E;m.getUniforms().setValue(s,"morphTargetBaseInfluence",R),m.getUniforms().setValue(s,"morphTargetInfluences",d)}m.getUniforms().setValue(s,"morphTargetsTexture",g.texture,i),m.getUniforms().setValue(s,"morphTargetsTextureSize",g.size)}return{update:c}}function fR(s,e,i,r,l){let c=new WeakMap;function f(d){const _=l.render.frame,v=d.geometry,g=e.get(d,v);if(c.get(g)!==_&&(e.update(g),c.set(g,_)),d.isInstancedMesh&&(d.hasEventListener("dispose",m)===!1&&d.addEventListener("dispose",m),c.get(d)!==_&&(i.update(d.instanceMatrix,s.ARRAY_BUFFER),d.instanceColor!==null&&i.update(d.instanceColor,s.ARRAY_BUFFER),c.set(d,_))),d.isSkinnedMesh){const M=d.skeleton;c.get(M)!==_&&(M.update(),c.set(M,_))}return g}function p(){c=new WeakMap}function m(d){const _=d.target;_.removeEventListener("dispose",m),r.releaseStatesOfObject(_),i.remove(_.instanceMatrix),_.instanceColor!==null&&i.remove(_.instanceColor)}return{update:f,dispose:p}}const hR={[$v]:"LINEAR_TONE_MAPPING",[ex]:"REINHARD_TONE_MAPPING",[tx]:"CINEON_TONE_MAPPING",[nx]:"ACES_FILMIC_TONE_MAPPING",[ax]:"AGX_TONE_MAPPING",[sx]:"NEUTRAL_TONE_MAPPING",[ix]:"CUSTOM_TONE_MAPPING"};function dR(s,e,i,r,l){const c=new Yi(e,i,{type:s,depthBuffer:r,stencilBuffer:l}),f=new Yi(e,i,{type:Ca,depthBuffer:!1,stencilBuffer:!1}),p=new Fi;p.setAttribute("position",new Aa([-1,3,0,-1,-1,0,3,-1,0],3)),p.setAttribute("uv",new Aa([0,2,0,0,2,0],2));const m=new rT({uniforms:{tDiffuse:{value:null}},vertexShader:`
			precision highp float;

			uniform mat4 modelViewMatrix;
			uniform mat4 projectionMatrix;

			attribute vec3 position;
			attribute vec2 uv;

			varying vec2 vUv;

			void main() {
				vUv = uv;
				gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
			}`,fragmentShader:`
			precision highp float;

			uniform sampler2D tDiffuse;

			varying vec2 vUv;

			#include <tonemapping_pars_fragment>
			#include <colorspace_pars_fragment>

			void main() {
				gl_FragColor = texture2D( tDiffuse, vUv );

				#ifdef LINEAR_TONE_MAPPING
					gl_FragColor.rgb = LinearToneMapping( gl_FragColor.rgb );
				#elif defined( REINHARD_TONE_MAPPING )
					gl_FragColor.rgb = ReinhardToneMapping( gl_FragColor.rgb );
				#elif defined( CINEON_TONE_MAPPING )
					gl_FragColor.rgb = CineonToneMapping( gl_FragColor.rgb );
				#elif defined( ACES_FILMIC_TONE_MAPPING )
					gl_FragColor.rgb = ACESFilmicToneMapping( gl_FragColor.rgb );
				#elif defined( AGX_TONE_MAPPING )
					gl_FragColor.rgb = AgXToneMapping( gl_FragColor.rgb );
				#elif defined( NEUTRAL_TONE_MAPPING )
					gl_FragColor.rgb = NeutralToneMapping( gl_FragColor.rgb );
				#elif defined( CUSTOM_TONE_MAPPING )
					gl_FragColor.rgb = CustomToneMapping( gl_FragColor.rgb );
				#endif

				#ifdef SRGB_TRANSFER
					gl_FragColor = sRGBTransferOETF( gl_FragColor );
				#endif
			}`,depthTest:!1,depthWrite:!1}),d=new Na(p,m),_=new Ax(-1,1,1,-1,0,1);let v=null,g=null,M=!1,E,R=null,x=[],y=!1;this.setSize=function(T,U){c.setSize(T,U),f.setSize(T,U);for(let P=0;P<x.length;P++){const V=x[P];V.setSize&&V.setSize(T,U)}},this.setEffects=function(T){x=T,y=x.length>0&&x[0].isRenderPass===!0;const U=c.width,P=c.height;for(let V=0;V<x.length;V++){const H=x[V];H.setSize&&H.setSize(U,P)}},this.begin=function(T,U){if(M||T.toneMapping===qi&&x.length===0)return!1;if(R=U,U!==null){const P=U.width,V=U.height;(c.width!==P||c.height!==V)&&this.setSize(P,V)}return y===!1&&T.setRenderTarget(c),E=T.toneMapping,T.toneMapping=qi,!0},this.hasRenderPass=function(){return y},this.end=function(T,U){T.toneMapping=E,M=!0;let P=c,V=f;for(let H=0;H<x.length;H++){const z=x[H];if(z.enabled!==!1&&(z.render(T,V,P,U),z.needsSwap!==!1)){const A=P;P=V,V=A}}if(v!==T.outputColorSpace||g!==T.toneMapping){v=T.outputColorSpace,g=T.toneMapping,m.defines={},Rt.getTransfer(v)===Bt&&(m.defines.SRGB_TRANSFER="");const H=hR[g];H&&(m.defines[H]=""),m.needsUpdate=!0}m.uniforms.tDiffuse.value=P.texture,T.setRenderTarget(R),T.render(d,_),R=null,M=!1},this.isCompositing=function(){return M},this.dispose=function(){c.dispose(),f.dispose(),p.dispose(),m.dispose()}}const wx=new Bn,fp=new cl(1,1),Dx=new mx,Nx=new Fb,Ux=new Mx,hv=[],dv=[],pv=new Float32Array(16),mv=new Float32Array(9),gv=new Float32Array(4);function eo(s,e,i){const r=s[0];if(r<=0||r>0)return s;const l=e*i;let c=hv[l];if(c===void 0&&(c=new Float32Array(l),hv[l]=c),e!==0){r.toArray(c,0);for(let f=1,p=0;f!==e;++f)p+=i,s[f].toArray(c,p)}return c}function xn(s,e){if(s.length!==e.length)return!1;for(let i=0,r=s.length;i<r;i++)if(s[i]!==e[i])return!1;return!0}function yn(s,e){for(let i=0,r=e.length;i<r;i++)s[i]=e[i]}function Eu(s,e){let i=dv[e];i===void 0&&(i=new Int32Array(e),dv[e]=i);for(let r=0;r!==e;++r)i[r]=s.allocateTextureUnit();return i}function pR(s,e){const i=this.cache;i[0]!==e&&(s.uniform1f(this.addr,e),i[0]=e)}function mR(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y)&&(s.uniform2f(this.addr,e.x,e.y),i[0]=e.x,i[1]=e.y);else{if(xn(i,e))return;s.uniform2fv(this.addr,e),yn(i,e)}}function gR(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z)&&(s.uniform3f(this.addr,e.x,e.y,e.z),i[0]=e.x,i[1]=e.y,i[2]=e.z);else if(e.r!==void 0)(i[0]!==e.r||i[1]!==e.g||i[2]!==e.b)&&(s.uniform3f(this.addr,e.r,e.g,e.b),i[0]=e.r,i[1]=e.g,i[2]=e.b);else{if(xn(i,e))return;s.uniform3fv(this.addr,e),yn(i,e)}}function _R(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z||i[3]!==e.w)&&(s.uniform4f(this.addr,e.x,e.y,e.z,e.w),i[0]=e.x,i[1]=e.y,i[2]=e.z,i[3]=e.w);else{if(xn(i,e))return;s.uniform4fv(this.addr,e),yn(i,e)}}function vR(s,e){const i=this.cache,r=e.elements;if(r===void 0){if(xn(i,e))return;s.uniformMatrix2fv(this.addr,!1,e),yn(i,e)}else{if(xn(i,r))return;gv.set(r),s.uniformMatrix2fv(this.addr,!1,gv),yn(i,r)}}function xR(s,e){const i=this.cache,r=e.elements;if(r===void 0){if(xn(i,e))return;s.uniformMatrix3fv(this.addr,!1,e),yn(i,e)}else{if(xn(i,r))return;mv.set(r),s.uniformMatrix3fv(this.addr,!1,mv),yn(i,r)}}function yR(s,e){const i=this.cache,r=e.elements;if(r===void 0){if(xn(i,e))return;s.uniformMatrix4fv(this.addr,!1,e),yn(i,e)}else{if(xn(i,r))return;pv.set(r),s.uniformMatrix4fv(this.addr,!1,pv),yn(i,r)}}function SR(s,e){const i=this.cache;i[0]!==e&&(s.uniform1i(this.addr,e),i[0]=e)}function MR(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y)&&(s.uniform2i(this.addr,e.x,e.y),i[0]=e.x,i[1]=e.y);else{if(xn(i,e))return;s.uniform2iv(this.addr,e),yn(i,e)}}function ER(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z)&&(s.uniform3i(this.addr,e.x,e.y,e.z),i[0]=e.x,i[1]=e.y,i[2]=e.z);else{if(xn(i,e))return;s.uniform3iv(this.addr,e),yn(i,e)}}function bR(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z||i[3]!==e.w)&&(s.uniform4i(this.addr,e.x,e.y,e.z,e.w),i[0]=e.x,i[1]=e.y,i[2]=e.z,i[3]=e.w);else{if(xn(i,e))return;s.uniform4iv(this.addr,e),yn(i,e)}}function TR(s,e){const i=this.cache;i[0]!==e&&(s.uniform1ui(this.addr,e),i[0]=e)}function AR(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y)&&(s.uniform2ui(this.addr,e.x,e.y),i[0]=e.x,i[1]=e.y);else{if(xn(i,e))return;s.uniform2uiv(this.addr,e),yn(i,e)}}function RR(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z)&&(s.uniform3ui(this.addr,e.x,e.y,e.z),i[0]=e.x,i[1]=e.y,i[2]=e.z);else{if(xn(i,e))return;s.uniform3uiv(this.addr,e),yn(i,e)}}function CR(s,e){const i=this.cache;if(e.x!==void 0)(i[0]!==e.x||i[1]!==e.y||i[2]!==e.z||i[3]!==e.w)&&(s.uniform4ui(this.addr,e.x,e.y,e.z,e.w),i[0]=e.x,i[1]=e.y,i[2]=e.z,i[3]=e.w);else{if(xn(i,e))return;s.uniform4uiv(this.addr,e),yn(i,e)}}function wR(s,e,i){const r=this.cache,l=i.allocateTextureUnit();r[0]!==l&&(s.uniform1i(this.addr,l),r[0]=l);let c;this.type===s.SAMPLER_2D_SHADOW?(fp.compareFunction=i.isReversedDepthBuffer()?wp:Cp,c=fp):c=wx,i.setTexture2D(e||c,l)}function DR(s,e,i){const r=this.cache,l=i.allocateTextureUnit();r[0]!==l&&(s.uniform1i(this.addr,l),r[0]=l),i.setTexture3D(e||Nx,l)}function NR(s,e,i){const r=this.cache,l=i.allocateTextureUnit();r[0]!==l&&(s.uniform1i(this.addr,l),r[0]=l),i.setTextureCube(e||Ux,l)}function UR(s,e,i){const r=this.cache,l=i.allocateTextureUnit();r[0]!==l&&(s.uniform1i(this.addr,l),r[0]=l),i.setTexture2DArray(e||Dx,l)}function LR(s){switch(s){case 5126:return pR;case 35664:return mR;case 35665:return gR;case 35666:return _R;case 35674:return vR;case 35675:return xR;case 35676:return yR;case 5124:case 35670:return SR;case 35667:case 35671:return MR;case 35668:case 35672:return ER;case 35669:case 35673:return bR;case 5125:return TR;case 36294:return AR;case 36295:return RR;case 36296:return CR;case 35678:case 36198:case 36298:case 36306:case 35682:return wR;case 35679:case 36299:case 36307:return DR;case 35680:case 36300:case 36308:case 36293:return NR;case 36289:case 36303:case 36311:case 36292:return UR}}function OR(s,e){s.uniform1fv(this.addr,e)}function PR(s,e){const i=eo(e,this.size,2);s.uniform2fv(this.addr,i)}function FR(s,e){const i=eo(e,this.size,3);s.uniform3fv(this.addr,i)}function IR(s,e){const i=eo(e,this.size,4);s.uniform4fv(this.addr,i)}function zR(s,e){const i=eo(e,this.size,4);s.uniformMatrix2fv(this.addr,!1,i)}function BR(s,e){const i=eo(e,this.size,9);s.uniformMatrix3fv(this.addr,!1,i)}function HR(s,e){const i=eo(e,this.size,16);s.uniformMatrix4fv(this.addr,!1,i)}function GR(s,e){s.uniform1iv(this.addr,e)}function VR(s,e){s.uniform2iv(this.addr,e)}function kR(s,e){s.uniform3iv(this.addr,e)}function jR(s,e){s.uniform4iv(this.addr,e)}function XR(s,e){s.uniform1uiv(this.addr,e)}function WR(s,e){s.uniform2uiv(this.addr,e)}function qR(s,e){s.uniform3uiv(this.addr,e)}function YR(s,e){s.uniform4uiv(this.addr,e)}function ZR(s,e,i){const r=this.cache,l=e.length,c=Eu(i,l);xn(r,c)||(s.uniform1iv(this.addr,c),yn(r,c));let f;this.type===s.SAMPLER_2D_SHADOW?f=fp:f=wx;for(let p=0;p!==l;++p)i.setTexture2D(e[p]||f,c[p])}function KR(s,e,i){const r=this.cache,l=e.length,c=Eu(i,l);xn(r,c)||(s.uniform1iv(this.addr,c),yn(r,c));for(let f=0;f!==l;++f)i.setTexture3D(e[f]||Nx,c[f])}function QR(s,e,i){const r=this.cache,l=e.length,c=Eu(i,l);xn(r,c)||(s.uniform1iv(this.addr,c),yn(r,c));for(let f=0;f!==l;++f)i.setTextureCube(e[f]||Ux,c[f])}function JR(s,e,i){const r=this.cache,l=e.length,c=Eu(i,l);xn(r,c)||(s.uniform1iv(this.addr,c),yn(r,c));for(let f=0;f!==l;++f)i.setTexture2DArray(e[f]||Dx,c[f])}function $R(s){switch(s){case 5126:return OR;case 35664:return PR;case 35665:return FR;case 35666:return IR;case 35674:return zR;case 35675:return BR;case 35676:return HR;case 5124:case 35670:return GR;case 35667:case 35671:return VR;case 35668:case 35672:return kR;case 35669:case 35673:return jR;case 5125:return XR;case 36294:return WR;case 36295:return qR;case 36296:return YR;case 35678:case 36198:case 36298:case 36306:case 35682:return ZR;case 35679:case 36299:case 36307:return KR;case 35680:case 36300:case 36308:case 36293:return QR;case 36289:case 36303:case 36311:case 36292:return JR}}class eC{constructor(e,i,r){this.id=e,this.addr=r,this.cache=[],this.type=i.type,this.setValue=LR(i.type)}}class tC{constructor(e,i,r){this.id=e,this.addr=r,this.cache=[],this.type=i.type,this.size=i.size,this.setValue=$R(i.type)}}class nC{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,i,r){const l=this.seq;for(let c=0,f=l.length;c!==f;++c){const p=l[c];p.setValue(e,i[p.id],r)}}}const dd=/(\w+)(\])?(\[|\.)?/g;function _v(s,e){s.seq.push(e),s.map[e.id]=e}function iC(s,e,i){const r=s.name,l=r.length;for(dd.lastIndex=0;;){const c=dd.exec(r),f=dd.lastIndex;let p=c[1];const m=c[2]==="]",d=c[3];if(m&&(p=p|0),d===void 0||d==="["&&f+2===l){_v(i,d===void 0?new eC(p,s,e):new tC(p,s,e));break}else{let v=i.map[p];v===void 0&&(v=new nC(p),_v(i,v)),i=v}}}class uu{constructor(e,i){this.seq=[],this.map={};const r=e.getProgramParameter(i,e.ACTIVE_UNIFORMS);for(let f=0;f<r;++f){const p=e.getActiveUniform(i,f),m=e.getUniformLocation(i,p.name);iC(p,m,this)}const l=[],c=[];for(const f of this.seq)f.type===e.SAMPLER_2D_SHADOW||f.type===e.SAMPLER_CUBE_SHADOW||f.type===e.SAMPLER_2D_ARRAY_SHADOW?l.push(f):c.push(f);l.length>0&&(this.seq=l.concat(c))}setValue(e,i,r,l){const c=this.map[i];c!==void 0&&c.setValue(e,r,l)}setOptional(e,i,r){const l=i[r];l!==void 0&&this.setValue(e,r,l)}static upload(e,i,r,l){for(let c=0,f=i.length;c!==f;++c){const p=i[c],m=r[p.id];m.needsUpdate!==!1&&p.setValue(e,m.value,l)}}static seqWithValue(e,i){const r=[];for(let l=0,c=e.length;l!==c;++l){const f=e[l];f.id in i&&r.push(f)}return r}}function vv(s,e,i){const r=s.createShader(e);return s.shaderSource(r,i),s.compileShader(r),r}const aC=37297;let sC=0;function rC(s,e){const i=s.split(`
`),r=[],l=Math.max(e-6,0),c=Math.min(e+6,i.length);for(let f=l;f<c;f++){const p=f+1;r.push(`${p===e?">":" "} ${p}: ${i[f]}`)}return r.join(`
`)}const xv=new dt;function oC(s){Rt._getMatrix(xv,Rt.workingColorSpace,s);const e=`mat3( ${xv.elements.map(i=>i.toFixed(4))} )`;switch(Rt.getTransfer(s)){case hu:return[e,"LinearTransferOETF"];case Bt:return[e,"sRGBTransferOETF"];default:return st("WebGLProgram: Unsupported color space: ",s),[e,"LinearTransferOETF"]}}function yv(s,e,i){const r=s.getShaderParameter(e,s.COMPILE_STATUS),c=(s.getShaderInfoLog(e)||"").trim();if(r&&c==="")return"";const f=/ERROR: 0:(\d+)/.exec(c);if(f){const p=parseInt(f[1]);return i.toUpperCase()+`

`+c+`

`+rC(s.getShaderSource(e),p)}else return c}function lC(s,e){const i=oC(e);return[`vec4 ${s}( vec4 value ) {`,`	return ${i[1]}( vec4( value.rgb * ${i[0]}, value.a ) );`,"}"].join(`
`)}const cC={[$v]:"Linear",[ex]:"Reinhard",[tx]:"Cineon",[nx]:"ACESFilmic",[ax]:"AgX",[sx]:"Neutral",[ix]:"Custom"};function uC(s,e){const i=cC[e];return i===void 0?(st("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+s+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+s+"( vec3 color ) { return "+i+"ToneMapping( color ); }"}const eu=new se;function fC(){Rt.getLuminanceCoefficients(eu);const s=eu.x.toFixed(4),e=eu.y.toFixed(4),i=eu.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${s}, ${e}, ${i} );`,"	return dot( weights, rgb );","}"].join(`
`)}function hC(s){return[s.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",s.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(il).join(`
`)}function dC(s){const e=[];for(const i in s){const r=s[i];r!==!1&&e.push("#define "+i+" "+r)}return e.join(`
`)}function pC(s,e){const i={},r=s.getProgramParameter(e,s.ACTIVE_ATTRIBUTES);for(let l=0;l<r;l++){const c=s.getActiveAttrib(e,l),f=c.name;let p=1;c.type===s.FLOAT_MAT2&&(p=2),c.type===s.FLOAT_MAT3&&(p=3),c.type===s.FLOAT_MAT4&&(p=4),i[f]={type:c.type,location:s.getAttribLocation(e,f),locationSize:p}}return i}function il(s){return s!==""}function Sv(s,e){const i=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return s.replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,i).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function Mv(s,e){return s.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}const mC=/^[ \t]*#include +<([\w\d./]+)>/gm;function hp(s){return s.replace(mC,_C)}const gC=new Map;function _C(s,e){let i=pt[e];if(i===void 0){const r=gC.get(e);if(r!==void 0)i=pt[r],st('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,r);else throw new Error("Can not resolve #include <"+e+">")}return hp(i)}const vC=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function Ev(s){return s.replace(vC,xC)}function xC(s,e,i,r){let l="";for(let c=parseInt(e);c<parseInt(i);c++)l+=r.replace(/\[\s*i\s*\]/g,"[ "+c+" ]").replace(/UNROLLED_LOOP_INDEX/g,c);return l}function bv(s){let e=`precision ${s.precision} float;
	precision ${s.precision} int;
	precision ${s.precision} sampler2D;
	precision ${s.precision} samplerCube;
	precision ${s.precision} sampler3D;
	precision ${s.precision} sampler2DArray;
	precision ${s.precision} sampler2DShadow;
	precision ${s.precision} samplerCubeShadow;
	precision ${s.precision} sampler2DArrayShadow;
	precision ${s.precision} isampler2D;
	precision ${s.precision} isampler3D;
	precision ${s.precision} isamplerCube;
	precision ${s.precision} isampler2DArray;
	precision ${s.precision} usampler2D;
	precision ${s.precision} usampler3D;
	precision ${s.precision} usamplerCube;
	precision ${s.precision} usampler2DArray;
	`;return s.precision==="highp"?e+=`
#define HIGH_PRECISION`:s.precision==="mediump"?e+=`
#define MEDIUM_PRECISION`:s.precision==="lowp"&&(e+=`
#define LOW_PRECISION`),e}const yC={[au]:"SHADOWMAP_TYPE_PCF",[nl]:"SHADOWMAP_TYPE_VSM"};function SC(s){return yC[s.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}const MC={[js]:"ENVMAP_TYPE_CUBE",[qr]:"ENVMAP_TYPE_CUBE",[vu]:"ENVMAP_TYPE_CUBE_UV"};function EC(s){return s.envMap===!1?"ENVMAP_TYPE_CUBE":MC[s.envMapMode]||"ENVMAP_TYPE_CUBE"}const bC={[qr]:"ENVMAP_MODE_REFRACTION"};function TC(s){return s.envMap===!1?"ENVMAP_MODE_REFLECTION":bC[s.envMapMode]||"ENVMAP_MODE_REFLECTION"}const AC={[Jv]:"ENVMAP_BLENDING_MULTIPLY",[db]:"ENVMAP_BLENDING_MIX",[pb]:"ENVMAP_BLENDING_ADD"};function RC(s){return s.envMap===!1?"ENVMAP_BLENDING_NONE":AC[s.combine]||"ENVMAP_BLENDING_NONE"}function CC(s){const e=s.envMapCubeUVHeight;if(e===null)return null;const i=Math.log2(e)-2,r=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,i),112)),texelHeight:r,maxMip:i}}function wC(s,e,i,r){const l=s.getContext(),c=i.defines;let f=i.vertexShader,p=i.fragmentShader;const m=SC(i),d=EC(i),_=TC(i),v=RC(i),g=CC(i),M=hC(i),E=dC(c),R=l.createProgram();let x,y,T=i.glslVersion?"#version "+i.glslVersion+`
`:"";i.isRawShaderMaterial?(x=["#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E].filter(il).join(`
`),x.length>0&&(x+=`
`),y=["#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E].filter(il).join(`
`),y.length>0&&(y+=`
`)):(x=[bv(i),"#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E,i.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",i.batching?"#define USE_BATCHING":"",i.batchingColor?"#define USE_BATCHING_COLOR":"",i.instancing?"#define USE_INSTANCING":"",i.instancingColor?"#define USE_INSTANCING_COLOR":"",i.instancingMorph?"#define USE_INSTANCING_MORPH":"",i.useFog&&i.fog?"#define USE_FOG":"",i.useFog&&i.fogExp2?"#define FOG_EXP2":"",i.map?"#define USE_MAP":"",i.envMap?"#define USE_ENVMAP":"",i.envMap?"#define "+_:"",i.lightMap?"#define USE_LIGHTMAP":"",i.aoMap?"#define USE_AOMAP":"",i.bumpMap?"#define USE_BUMPMAP":"",i.normalMap?"#define USE_NORMALMAP":"",i.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",i.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",i.displacementMap?"#define USE_DISPLACEMENTMAP":"",i.emissiveMap?"#define USE_EMISSIVEMAP":"",i.anisotropy?"#define USE_ANISOTROPY":"",i.anisotropyMap?"#define USE_ANISOTROPYMAP":"",i.clearcoatMap?"#define USE_CLEARCOATMAP":"",i.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",i.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",i.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",i.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",i.specularMap?"#define USE_SPECULARMAP":"",i.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",i.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",i.roughnessMap?"#define USE_ROUGHNESSMAP":"",i.metalnessMap?"#define USE_METALNESSMAP":"",i.alphaMap?"#define USE_ALPHAMAP":"",i.alphaHash?"#define USE_ALPHAHASH":"",i.transmission?"#define USE_TRANSMISSION":"",i.transmissionMap?"#define USE_TRANSMISSIONMAP":"",i.thicknessMap?"#define USE_THICKNESSMAP":"",i.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",i.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",i.mapUv?"#define MAP_UV "+i.mapUv:"",i.alphaMapUv?"#define ALPHAMAP_UV "+i.alphaMapUv:"",i.lightMapUv?"#define LIGHTMAP_UV "+i.lightMapUv:"",i.aoMapUv?"#define AOMAP_UV "+i.aoMapUv:"",i.emissiveMapUv?"#define EMISSIVEMAP_UV "+i.emissiveMapUv:"",i.bumpMapUv?"#define BUMPMAP_UV "+i.bumpMapUv:"",i.normalMapUv?"#define NORMALMAP_UV "+i.normalMapUv:"",i.displacementMapUv?"#define DISPLACEMENTMAP_UV "+i.displacementMapUv:"",i.metalnessMapUv?"#define METALNESSMAP_UV "+i.metalnessMapUv:"",i.roughnessMapUv?"#define ROUGHNESSMAP_UV "+i.roughnessMapUv:"",i.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+i.anisotropyMapUv:"",i.clearcoatMapUv?"#define CLEARCOATMAP_UV "+i.clearcoatMapUv:"",i.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+i.clearcoatNormalMapUv:"",i.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+i.clearcoatRoughnessMapUv:"",i.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+i.iridescenceMapUv:"",i.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+i.iridescenceThicknessMapUv:"",i.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+i.sheenColorMapUv:"",i.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+i.sheenRoughnessMapUv:"",i.specularMapUv?"#define SPECULARMAP_UV "+i.specularMapUv:"",i.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+i.specularColorMapUv:"",i.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+i.specularIntensityMapUv:"",i.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+i.transmissionMapUv:"",i.thicknessMapUv?"#define THICKNESSMAP_UV "+i.thicknessMapUv:"",i.vertexTangents&&i.flatShading===!1?"#define USE_TANGENT":"",i.vertexColors?"#define USE_COLOR":"",i.vertexAlphas?"#define USE_COLOR_ALPHA":"",i.vertexUv1s?"#define USE_UV1":"",i.vertexUv2s?"#define USE_UV2":"",i.vertexUv3s?"#define USE_UV3":"",i.pointsUvs?"#define USE_POINTS_UV":"",i.flatShading?"#define FLAT_SHADED":"",i.skinning?"#define USE_SKINNING":"",i.morphTargets?"#define USE_MORPHTARGETS":"",i.morphNormals&&i.flatShading===!1?"#define USE_MORPHNORMALS":"",i.morphColors?"#define USE_MORPHCOLORS":"",i.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+i.morphTextureStride:"",i.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+i.morphTargetsCount:"",i.doubleSided?"#define DOUBLE_SIDED":"",i.flipSided?"#define FLIP_SIDED":"",i.shadowMapEnabled?"#define USE_SHADOWMAP":"",i.shadowMapEnabled?"#define "+m:"",i.sizeAttenuation?"#define USE_SIZEATTENUATION":"",i.numLightProbes>0?"#define USE_LIGHT_PROBES":"",i.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",i.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(il).join(`
`),y=[bv(i),"#define SHADER_TYPE "+i.shaderType,"#define SHADER_NAME "+i.shaderName,E,i.useFog&&i.fog?"#define USE_FOG":"",i.useFog&&i.fogExp2?"#define FOG_EXP2":"",i.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",i.map?"#define USE_MAP":"",i.matcap?"#define USE_MATCAP":"",i.envMap?"#define USE_ENVMAP":"",i.envMap?"#define "+d:"",i.envMap?"#define "+_:"",i.envMap?"#define "+v:"",g?"#define CUBEUV_TEXEL_WIDTH "+g.texelWidth:"",g?"#define CUBEUV_TEXEL_HEIGHT "+g.texelHeight:"",g?"#define CUBEUV_MAX_MIP "+g.maxMip+".0":"",i.lightMap?"#define USE_LIGHTMAP":"",i.aoMap?"#define USE_AOMAP":"",i.bumpMap?"#define USE_BUMPMAP":"",i.normalMap?"#define USE_NORMALMAP":"",i.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",i.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",i.emissiveMap?"#define USE_EMISSIVEMAP":"",i.anisotropy?"#define USE_ANISOTROPY":"",i.anisotropyMap?"#define USE_ANISOTROPYMAP":"",i.clearcoat?"#define USE_CLEARCOAT":"",i.clearcoatMap?"#define USE_CLEARCOATMAP":"",i.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",i.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",i.dispersion?"#define USE_DISPERSION":"",i.iridescence?"#define USE_IRIDESCENCE":"",i.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",i.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",i.specularMap?"#define USE_SPECULARMAP":"",i.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",i.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",i.roughnessMap?"#define USE_ROUGHNESSMAP":"",i.metalnessMap?"#define USE_METALNESSMAP":"",i.alphaMap?"#define USE_ALPHAMAP":"",i.alphaTest?"#define USE_ALPHATEST":"",i.alphaHash?"#define USE_ALPHAHASH":"",i.sheen?"#define USE_SHEEN":"",i.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",i.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",i.transmission?"#define USE_TRANSMISSION":"",i.transmissionMap?"#define USE_TRANSMISSIONMAP":"",i.thicknessMap?"#define USE_THICKNESSMAP":"",i.vertexTangents&&i.flatShading===!1?"#define USE_TANGENT":"",i.vertexColors||i.instancingColor?"#define USE_COLOR":"",i.vertexAlphas||i.batchingColor?"#define USE_COLOR_ALPHA":"",i.vertexUv1s?"#define USE_UV1":"",i.vertexUv2s?"#define USE_UV2":"",i.vertexUv3s?"#define USE_UV3":"",i.pointsUvs?"#define USE_POINTS_UV":"",i.gradientMap?"#define USE_GRADIENTMAP":"",i.flatShading?"#define FLAT_SHADED":"",i.doubleSided?"#define DOUBLE_SIDED":"",i.flipSided?"#define FLIP_SIDED":"",i.shadowMapEnabled?"#define USE_SHADOWMAP":"",i.shadowMapEnabled?"#define "+m:"",i.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",i.numLightProbes>0?"#define USE_LIGHT_PROBES":"",i.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",i.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",i.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",i.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",i.toneMapping!==qi?"#define TONE_MAPPING":"",i.toneMapping!==qi?pt.tonemapping_pars_fragment:"",i.toneMapping!==qi?uC("toneMapping",i.toneMapping):"",i.dithering?"#define DITHERING":"",i.opaque?"#define OPAQUE":"",pt.colorspace_pars_fragment,lC("linearToOutputTexel",i.outputColorSpace),fC(),i.useDepthPacking?"#define DEPTH_PACKING "+i.depthPacking:"",`
`].filter(il).join(`
`)),f=hp(f),f=Sv(f,i),f=Mv(f,i),p=hp(p),p=Sv(p,i),p=Mv(p,i),f=Ev(f),p=Ev(p),i.isRawShaderMaterial!==!0&&(T=`#version 300 es
`,x=[M,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+x,y=["#define varying in",i.glslVersion===P0?"":"layout(location = 0) out highp vec4 pc_fragColor;",i.glslVersion===P0?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+y);const U=T+x+f,P=T+y+p,V=vv(l,l.VERTEX_SHADER,U),H=vv(l,l.FRAGMENT_SHADER,P);l.attachShader(R,V),l.attachShader(R,H),i.index0AttributeName!==void 0?l.bindAttribLocation(R,0,i.index0AttributeName):i.morphTargets===!0&&l.bindAttribLocation(R,0,"position"),l.linkProgram(R);function z(w){if(s.debug.checkShaderErrors){const Y=l.getProgramInfoLog(R)||"",re=l.getShaderInfoLog(V)||"",fe=l.getShaderInfoLog(H)||"",ee=Y.trim(),I=re.trim(),B=fe.trim();let $=!0,Q=!0;if(l.getProgramParameter(R,l.LINK_STATUS)===!1)if($=!1,typeof s.debug.onShaderError=="function")s.debug.onShaderError(l,R,V,H);else{const de=yv(l,V,"vertex"),O=yv(l,H,"fragment");At("THREE.WebGLProgram: Shader Error "+l.getError()+" - VALIDATE_STATUS "+l.getProgramParameter(R,l.VALIDATE_STATUS)+`

Material Name: `+w.name+`
Material Type: `+w.type+`

Program Info Log: `+ee+`
`+de+`
`+O)}else ee!==""?st("WebGLProgram: Program Info Log:",ee):(I===""||B==="")&&(Q=!1);Q&&(w.diagnostics={runnable:$,programLog:ee,vertexShader:{log:I,prefix:x},fragmentShader:{log:B,prefix:y}})}l.deleteShader(V),l.deleteShader(H),A=new uu(l,R),L=pC(l,R)}let A;this.getUniforms=function(){return A===void 0&&z(this),A};let L;this.getAttributes=function(){return L===void 0&&z(this),L};let pe=i.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return pe===!1&&(pe=l.getProgramParameter(R,aC)),pe},this.destroy=function(){r.releaseStatesOfProgram(this),l.deleteProgram(R),this.program=void 0},this.type=i.shaderType,this.name=i.shaderName,this.id=sC++,this.cacheKey=e,this.usedTimes=1,this.program=R,this.vertexShader=V,this.fragmentShader=H,this}let DC=0;class NC{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e){const i=e.vertexShader,r=e.fragmentShader,l=this._getShaderStage(i),c=this._getShaderStage(r),f=this._getShaderCacheForMaterial(e);return f.has(l)===!1&&(f.add(l),l.usedTimes++),f.has(c)===!1&&(f.add(c),c.usedTimes++),this}remove(e){const i=this.materialCache.get(e);for(const r of i)r.usedTimes--,r.usedTimes===0&&this.shaderCache.delete(r.code);return this.materialCache.delete(e),this}getVertexShaderID(e){return this._getShaderStage(e.vertexShader).id}getFragmentShaderID(e){return this._getShaderStage(e.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){const i=this.materialCache;let r=i.get(e);return r===void 0&&(r=new Set,i.set(e,r)),r}_getShaderStage(e){const i=this.shaderCache;let r=i.get(e);return r===void 0&&(r=new UC(e),i.set(e,r)),r}}class UC{constructor(e){this.id=DC++,this.code=e,this.usedTimes=0}}function LC(s,e,i,r,l,c){const f=new Np,p=new NC,m=new Set,d=[],_=new Map,v=r.logarithmicDepthBuffer;let g=r.precision;const M={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function E(A){return m.add(A),A===0?"uv":`uv${A}`}function R(A,L,pe,w,Y){const re=w.fog,fe=Y.geometry,ee=A.isMeshStandardMaterial||A.isMeshLambertMaterial||A.isMeshPhongMaterial?w.environment:null,I=A.isMeshStandardMaterial||A.isMeshLambertMaterial&&!A.envMap||A.isMeshPhongMaterial&&!A.envMap,B=e.get(A.envMap||ee,I),$=B&&B.mapping===vu?B.image.height:null,Q=M[A.type];A.precision!==null&&(g=r.getMaxPrecision(A.precision),g!==A.precision&&st("WebGLProgram.getParameters:",A.precision,"not supported, using",g,"instead."));const de=fe.morphAttributes.position||fe.morphAttributes.normal||fe.morphAttributes.color,O=de!==void 0?de.length:0;let j=0;fe.morphAttributes.position!==void 0&&(j=1),fe.morphAttributes.normal!==void 0&&(j=2),fe.morphAttributes.color!==void 0&&(j=3);let ve,he,Ne,ie;if(Q){const Tt=ji[Q];ve=Tt.vertexShader,he=Tt.fragmentShader}else ve=A.vertexShader,he=A.fragmentShader,p.update(A),Ne=p.getVertexShaderID(A),ie=p.getFragmentShaderID(A);const Se=s.getRenderTarget(),Ae=s.state.buffers.depth.getReversed(),Ge=Y.isInstancedMesh===!0,Qe=Y.isBatchedMesh===!0,qe=!!A.map,$t=!!A.matcap,yt=!!B,gt=!!A.aoMap,Nt=!!A.lightMap,lt=!!A.bumpMap,Jt=!!A.normalMap,k=!!A.displacementMap,qt=!!A.emissiveMap,bt=!!A.metalnessMap,Ot=!!A.roughnessMap,Ye=A.anisotropy>0,F=A.clearcoat>0,b=A.dispersion>0,Z=A.iridescence>0,xe=A.sheen>0,Ee=A.transmission>0,ge=Ye&&!!A.anisotropyMap,Xe=F&&!!A.clearcoatMap,De=F&&!!A.clearcoatNormalMap,Je=F&&!!A.clearcoatRoughnessMap,tt=Z&&!!A.iridescenceMap,Re=Z&&!!A.iridescenceThicknessMap,be=xe&&!!A.sheenColorMap,Fe=xe&&!!A.sheenRoughnessMap,Pe=!!A.specularMap,Ie=!!A.specularColorMap,ut=!!A.specularIntensityMap,q=Ee&&!!A.transmissionMap,we=Ee&&!!A.thicknessMap,Ce=!!A.gradientMap,ze=!!A.alphaMap,Te=A.alphaTest>0,me=!!A.alphaHash,He=!!A.extensions;let it=qi;A.toneMapped&&(Se===null||Se.isXRRenderTarget===!0)&&(it=s.toneMapping);const Ft={shaderID:Q,shaderType:A.type,shaderName:A.name,vertexShader:ve,fragmentShader:he,defines:A.defines,customVertexShaderID:Ne,customFragmentShaderID:ie,isRawShaderMaterial:A.isRawShaderMaterial===!0,glslVersion:A.glslVersion,precision:g,batching:Qe,batchingColor:Qe&&Y._colorsTexture!==null,instancing:Ge,instancingColor:Ge&&Y.instanceColor!==null,instancingMorph:Ge&&Y.morphTexture!==null,outputColorSpace:Se===null?s.outputColorSpace:Se.isXRRenderTarget===!0?Se.texture.colorSpace:Zr,alphaToCoverage:!!A.alphaToCoverage,map:qe,matcap:$t,envMap:yt,envMapMode:yt&&B.mapping,envMapCubeUVHeight:$,aoMap:gt,lightMap:Nt,bumpMap:lt,normalMap:Jt,displacementMap:k,emissiveMap:qt,normalMapObjectSpace:Jt&&A.normalMapType===vb,normalMapTangentSpace:Jt&&A.normalMapType===_b,metalnessMap:bt,roughnessMap:Ot,anisotropy:Ye,anisotropyMap:ge,clearcoat:F,clearcoatMap:Xe,clearcoatNormalMap:De,clearcoatRoughnessMap:Je,dispersion:b,iridescence:Z,iridescenceMap:tt,iridescenceThicknessMap:Re,sheen:xe,sheenColorMap:be,sheenRoughnessMap:Fe,specularMap:Pe,specularColorMap:Ie,specularIntensityMap:ut,transmission:Ee,transmissionMap:q,thicknessMap:we,gradientMap:Ce,opaque:A.transparent===!1&&A.blending===jr&&A.alphaToCoverage===!1,alphaMap:ze,alphaTest:Te,alphaHash:me,combine:A.combine,mapUv:qe&&E(A.map.channel),aoMapUv:gt&&E(A.aoMap.channel),lightMapUv:Nt&&E(A.lightMap.channel),bumpMapUv:lt&&E(A.bumpMap.channel),normalMapUv:Jt&&E(A.normalMap.channel),displacementMapUv:k&&E(A.displacementMap.channel),emissiveMapUv:qt&&E(A.emissiveMap.channel),metalnessMapUv:bt&&E(A.metalnessMap.channel),roughnessMapUv:Ot&&E(A.roughnessMap.channel),anisotropyMapUv:ge&&E(A.anisotropyMap.channel),clearcoatMapUv:Xe&&E(A.clearcoatMap.channel),clearcoatNormalMapUv:De&&E(A.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:Je&&E(A.clearcoatRoughnessMap.channel),iridescenceMapUv:tt&&E(A.iridescenceMap.channel),iridescenceThicknessMapUv:Re&&E(A.iridescenceThicknessMap.channel),sheenColorMapUv:be&&E(A.sheenColorMap.channel),sheenRoughnessMapUv:Fe&&E(A.sheenRoughnessMap.channel),specularMapUv:Pe&&E(A.specularMap.channel),specularColorMapUv:Ie&&E(A.specularColorMap.channel),specularIntensityMapUv:ut&&E(A.specularIntensityMap.channel),transmissionMapUv:q&&E(A.transmissionMap.channel),thicknessMapUv:we&&E(A.thicknessMap.channel),alphaMapUv:ze&&E(A.alphaMap.channel),vertexTangents:!!fe.attributes.tangent&&(Jt||Ye),vertexColors:A.vertexColors,vertexAlphas:A.vertexColors===!0&&!!fe.attributes.color&&fe.attributes.color.itemSize===4,pointsUvs:Y.isPoints===!0&&!!fe.attributes.uv&&(qe||ze),fog:!!re,useFog:A.fog===!0,fogExp2:!!re&&re.isFogExp2,flatShading:A.wireframe===!1&&(A.flatShading===!0||fe.attributes.normal===void 0&&Jt===!1&&(A.isMeshLambertMaterial||A.isMeshPhongMaterial||A.isMeshStandardMaterial||A.isMeshPhysicalMaterial)),sizeAttenuation:A.sizeAttenuation===!0,logarithmicDepthBuffer:v,reversedDepthBuffer:Ae,skinning:Y.isSkinnedMesh===!0,morphTargets:fe.morphAttributes.position!==void 0,morphNormals:fe.morphAttributes.normal!==void 0,morphColors:fe.morphAttributes.color!==void 0,morphTargetsCount:O,morphTextureStride:j,numDirLights:L.directional.length,numPointLights:L.point.length,numSpotLights:L.spot.length,numSpotLightMaps:L.spotLightMap.length,numRectAreaLights:L.rectArea.length,numHemiLights:L.hemi.length,numDirLightShadows:L.directionalShadowMap.length,numPointLightShadows:L.pointShadowMap.length,numSpotLightShadows:L.spotShadowMap.length,numSpotLightShadowsWithMaps:L.numSpotLightShadowsWithMaps,numLightProbes:L.numLightProbes,numClippingPlanes:c.numPlanes,numClipIntersection:c.numIntersection,dithering:A.dithering,shadowMapEnabled:s.shadowMap.enabled&&pe.length>0,shadowMapType:s.shadowMap.type,toneMapping:it,decodeVideoTexture:qe&&A.map.isVideoTexture===!0&&Rt.getTransfer(A.map.colorSpace)===Bt,decodeVideoTextureEmissive:qt&&A.emissiveMap.isVideoTexture===!0&&Rt.getTransfer(A.emissiveMap.colorSpace)===Bt,premultipliedAlpha:A.premultipliedAlpha,doubleSided:A.side===Sa,flipSided:A.side===Zn,useDepthPacking:A.depthPacking>=0,depthPacking:A.depthPacking||0,index0AttributeName:A.index0AttributeName,extensionClipCullDistance:He&&A.extensions.clipCullDistance===!0&&i.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(He&&A.extensions.multiDraw===!0||Qe)&&i.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:i.has("KHR_parallel_shader_compile"),customProgramCacheKey:A.customProgramCacheKey()};return Ft.vertexUv1s=m.has(1),Ft.vertexUv2s=m.has(2),Ft.vertexUv3s=m.has(3),m.clear(),Ft}function x(A){const L=[];if(A.shaderID?L.push(A.shaderID):(L.push(A.customVertexShaderID),L.push(A.customFragmentShaderID)),A.defines!==void 0)for(const pe in A.defines)L.push(pe),L.push(A.defines[pe]);return A.isRawShaderMaterial===!1&&(y(L,A),T(L,A),L.push(s.outputColorSpace)),L.push(A.customProgramCacheKey),L.join()}function y(A,L){A.push(L.precision),A.push(L.outputColorSpace),A.push(L.envMapMode),A.push(L.envMapCubeUVHeight),A.push(L.mapUv),A.push(L.alphaMapUv),A.push(L.lightMapUv),A.push(L.aoMapUv),A.push(L.bumpMapUv),A.push(L.normalMapUv),A.push(L.displacementMapUv),A.push(L.emissiveMapUv),A.push(L.metalnessMapUv),A.push(L.roughnessMapUv),A.push(L.anisotropyMapUv),A.push(L.clearcoatMapUv),A.push(L.clearcoatNormalMapUv),A.push(L.clearcoatRoughnessMapUv),A.push(L.iridescenceMapUv),A.push(L.iridescenceThicknessMapUv),A.push(L.sheenColorMapUv),A.push(L.sheenRoughnessMapUv),A.push(L.specularMapUv),A.push(L.specularColorMapUv),A.push(L.specularIntensityMapUv),A.push(L.transmissionMapUv),A.push(L.thicknessMapUv),A.push(L.combine),A.push(L.fogExp2),A.push(L.sizeAttenuation),A.push(L.morphTargetsCount),A.push(L.morphAttributeCount),A.push(L.numDirLights),A.push(L.numPointLights),A.push(L.numSpotLights),A.push(L.numSpotLightMaps),A.push(L.numHemiLights),A.push(L.numRectAreaLights),A.push(L.numDirLightShadows),A.push(L.numPointLightShadows),A.push(L.numSpotLightShadows),A.push(L.numSpotLightShadowsWithMaps),A.push(L.numLightProbes),A.push(L.shadowMapType),A.push(L.toneMapping),A.push(L.numClippingPlanes),A.push(L.numClipIntersection),A.push(L.depthPacking)}function T(A,L){f.disableAll(),L.instancing&&f.enable(0),L.instancingColor&&f.enable(1),L.instancingMorph&&f.enable(2),L.matcap&&f.enable(3),L.envMap&&f.enable(4),L.normalMapObjectSpace&&f.enable(5),L.normalMapTangentSpace&&f.enable(6),L.clearcoat&&f.enable(7),L.iridescence&&f.enable(8),L.alphaTest&&f.enable(9),L.vertexColors&&f.enable(10),L.vertexAlphas&&f.enable(11),L.vertexUv1s&&f.enable(12),L.vertexUv2s&&f.enable(13),L.vertexUv3s&&f.enable(14),L.vertexTangents&&f.enable(15),L.anisotropy&&f.enable(16),L.alphaHash&&f.enable(17),L.batching&&f.enable(18),L.dispersion&&f.enable(19),L.batchingColor&&f.enable(20),L.gradientMap&&f.enable(21),A.push(f.mask),f.disableAll(),L.fog&&f.enable(0),L.useFog&&f.enable(1),L.flatShading&&f.enable(2),L.logarithmicDepthBuffer&&f.enable(3),L.reversedDepthBuffer&&f.enable(4),L.skinning&&f.enable(5),L.morphTargets&&f.enable(6),L.morphNormals&&f.enable(7),L.morphColors&&f.enable(8),L.premultipliedAlpha&&f.enable(9),L.shadowMapEnabled&&f.enable(10),L.doubleSided&&f.enable(11),L.flipSided&&f.enable(12),L.useDepthPacking&&f.enable(13),L.dithering&&f.enable(14),L.transmission&&f.enable(15),L.sheen&&f.enable(16),L.opaque&&f.enable(17),L.pointsUvs&&f.enable(18),L.decodeVideoTexture&&f.enable(19),L.decodeVideoTextureEmissive&&f.enable(20),L.alphaToCoverage&&f.enable(21),A.push(f.mask)}function U(A){const L=M[A.type];let pe;if(L){const w=ji[L];pe=iT.clone(w.uniforms)}else pe=A.uniforms;return pe}function P(A,L){let pe=_.get(L);return pe!==void 0?++pe.usedTimes:(pe=new wC(s,L,A,l),d.push(pe),_.set(L,pe)),pe}function V(A){if(--A.usedTimes===0){const L=d.indexOf(A);d[L]=d[d.length-1],d.pop(),_.delete(A.cacheKey),A.destroy()}}function H(A){p.remove(A)}function z(){p.dispose()}return{getParameters:R,getProgramCacheKey:x,getUniforms:U,acquireProgram:P,releaseProgram:V,releaseShaderCache:H,programs:d,dispose:z}}function OC(){let s=new WeakMap;function e(f){return s.has(f)}function i(f){let p=s.get(f);return p===void 0&&(p={},s.set(f,p)),p}function r(f){s.delete(f)}function l(f,p,m){s.get(f)[p]=m}function c(){s=new WeakMap}return{has:e,get:i,remove:r,update:l,dispose:c}}function PC(s,e){return s.groupOrder!==e.groupOrder?s.groupOrder-e.groupOrder:s.renderOrder!==e.renderOrder?s.renderOrder-e.renderOrder:s.material.id!==e.material.id?s.material.id-e.material.id:s.materialVariant!==e.materialVariant?s.materialVariant-e.materialVariant:s.z!==e.z?s.z-e.z:s.id-e.id}function Tv(s,e){return s.groupOrder!==e.groupOrder?s.groupOrder-e.groupOrder:s.renderOrder!==e.renderOrder?s.renderOrder-e.renderOrder:s.z!==e.z?e.z-s.z:s.id-e.id}function Av(){const s=[];let e=0;const i=[],r=[],l=[];function c(){e=0,i.length=0,r.length=0,l.length=0}function f(g){let M=0;return g.isInstancedMesh&&(M+=2),g.isSkinnedMesh&&(M+=1),M}function p(g,M,E,R,x,y){let T=s[e];return T===void 0?(T={id:g.id,object:g,geometry:M,material:E,materialVariant:f(g),groupOrder:R,renderOrder:g.renderOrder,z:x,group:y},s[e]=T):(T.id=g.id,T.object=g,T.geometry=M,T.material=E,T.materialVariant=f(g),T.groupOrder=R,T.renderOrder=g.renderOrder,T.z=x,T.group=y),e++,T}function m(g,M,E,R,x,y){const T=p(g,M,E,R,x,y);E.transmission>0?r.push(T):E.transparent===!0?l.push(T):i.push(T)}function d(g,M,E,R,x,y){const T=p(g,M,E,R,x,y);E.transmission>0?r.unshift(T):E.transparent===!0?l.unshift(T):i.unshift(T)}function _(g,M){i.length>1&&i.sort(g||PC),r.length>1&&r.sort(M||Tv),l.length>1&&l.sort(M||Tv)}function v(){for(let g=e,M=s.length;g<M;g++){const E=s[g];if(E.id===null)break;E.id=null,E.object=null,E.geometry=null,E.material=null,E.group=null}}return{opaque:i,transmissive:r,transparent:l,init:c,push:m,unshift:d,finish:v,sort:_}}function FC(){let s=new WeakMap;function e(r,l){const c=s.get(r);let f;return c===void 0?(f=new Av,s.set(r,[f])):l>=c.length?(f=new Av,c.push(f)):f=c[l],f}function i(){s=new WeakMap}return{get:e,dispose:i}}function IC(){const s={};return{get:function(e){if(s[e.id]!==void 0)return s[e.id];let i;switch(e.type){case"DirectionalLight":i={direction:new se,color:new Lt};break;case"SpotLight":i={position:new se,direction:new se,color:new Lt,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":i={position:new se,color:new Lt,distance:0,decay:0};break;case"HemisphereLight":i={direction:new se,skyColor:new Lt,groundColor:new Lt};break;case"RectAreaLight":i={color:new Lt,position:new se,halfWidth:new se,halfHeight:new se};break}return s[e.id]=i,i}}}function zC(){const s={};return{get:function(e){if(s[e.id]!==void 0)return s[e.id];let i;switch(e.type){case"DirectionalLight":i={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new mt};break;case"SpotLight":i={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new mt};break;case"PointLight":i={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new mt,shadowCameraNear:1,shadowCameraFar:1e3};break}return s[e.id]=i,i}}}let BC=0;function HC(s,e){return(e.castShadow?2:0)-(s.castShadow?2:0)+(e.map?1:0)-(s.map?1:0)}function GC(s){const e=new IC,i=zC(),r={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let d=0;d<9;d++)r.probe.push(new se);const l=new se,c=new nn,f=new nn;function p(d){let _=0,v=0,g=0;for(let L=0;L<9;L++)r.probe[L].set(0,0,0);let M=0,E=0,R=0,x=0,y=0,T=0,U=0,P=0,V=0,H=0,z=0;d.sort(HC);for(let L=0,pe=d.length;L<pe;L++){const w=d[L],Y=w.color,re=w.intensity,fe=w.distance;let ee=null;if(w.shadow&&w.shadow.map&&(w.shadow.map.texture.format===Yr?ee=w.shadow.map.texture:ee=w.shadow.map.depthTexture||w.shadow.map.texture),w.isAmbientLight)_+=Y.r*re,v+=Y.g*re,g+=Y.b*re;else if(w.isLightProbe){for(let I=0;I<9;I++)r.probe[I].addScaledVector(w.sh.coefficients[I],re);z++}else if(w.isDirectionalLight){const I=e.get(w);if(I.color.copy(w.color).multiplyScalar(w.intensity),w.castShadow){const B=w.shadow,$=i.get(w);$.shadowIntensity=B.intensity,$.shadowBias=B.bias,$.shadowNormalBias=B.normalBias,$.shadowRadius=B.radius,$.shadowMapSize=B.mapSize,r.directionalShadow[M]=$,r.directionalShadowMap[M]=ee,r.directionalShadowMatrix[M]=w.shadow.matrix,T++}r.directional[M]=I,M++}else if(w.isSpotLight){const I=e.get(w);I.position.setFromMatrixPosition(w.matrixWorld),I.color.copy(Y).multiplyScalar(re),I.distance=fe,I.coneCos=Math.cos(w.angle),I.penumbraCos=Math.cos(w.angle*(1-w.penumbra)),I.decay=w.decay,r.spot[R]=I;const B=w.shadow;if(w.map&&(r.spotLightMap[V]=w.map,V++,B.updateMatrices(w),w.castShadow&&H++),r.spotLightMatrix[R]=B.matrix,w.castShadow){const $=i.get(w);$.shadowIntensity=B.intensity,$.shadowBias=B.bias,$.shadowNormalBias=B.normalBias,$.shadowRadius=B.radius,$.shadowMapSize=B.mapSize,r.spotShadow[R]=$,r.spotShadowMap[R]=ee,P++}R++}else if(w.isRectAreaLight){const I=e.get(w);I.color.copy(Y).multiplyScalar(re),I.halfWidth.set(w.width*.5,0,0),I.halfHeight.set(0,w.height*.5,0),r.rectArea[x]=I,x++}else if(w.isPointLight){const I=e.get(w);if(I.color.copy(w.color).multiplyScalar(w.intensity),I.distance=w.distance,I.decay=w.decay,w.castShadow){const B=w.shadow,$=i.get(w);$.shadowIntensity=B.intensity,$.shadowBias=B.bias,$.shadowNormalBias=B.normalBias,$.shadowRadius=B.radius,$.shadowMapSize=B.mapSize,$.shadowCameraNear=B.camera.near,$.shadowCameraFar=B.camera.far,r.pointShadow[E]=$,r.pointShadowMap[E]=ee,r.pointShadowMatrix[E]=w.shadow.matrix,U++}r.point[E]=I,E++}else if(w.isHemisphereLight){const I=e.get(w);I.skyColor.copy(w.color).multiplyScalar(re),I.groundColor.copy(w.groundColor).multiplyScalar(re),r.hemi[y]=I,y++}}x>0&&(s.has("OES_texture_float_linear")===!0?(r.rectAreaLTC1=Oe.LTC_FLOAT_1,r.rectAreaLTC2=Oe.LTC_FLOAT_2):(r.rectAreaLTC1=Oe.LTC_HALF_1,r.rectAreaLTC2=Oe.LTC_HALF_2)),r.ambient[0]=_,r.ambient[1]=v,r.ambient[2]=g;const A=r.hash;(A.directionalLength!==M||A.pointLength!==E||A.spotLength!==R||A.rectAreaLength!==x||A.hemiLength!==y||A.numDirectionalShadows!==T||A.numPointShadows!==U||A.numSpotShadows!==P||A.numSpotMaps!==V||A.numLightProbes!==z)&&(r.directional.length=M,r.spot.length=R,r.rectArea.length=x,r.point.length=E,r.hemi.length=y,r.directionalShadow.length=T,r.directionalShadowMap.length=T,r.pointShadow.length=U,r.pointShadowMap.length=U,r.spotShadow.length=P,r.spotShadowMap.length=P,r.directionalShadowMatrix.length=T,r.pointShadowMatrix.length=U,r.spotLightMatrix.length=P+V-H,r.spotLightMap.length=V,r.numSpotLightShadowsWithMaps=H,r.numLightProbes=z,A.directionalLength=M,A.pointLength=E,A.spotLength=R,A.rectAreaLength=x,A.hemiLength=y,A.numDirectionalShadows=T,A.numPointShadows=U,A.numSpotShadows=P,A.numSpotMaps=V,A.numLightProbes=z,r.version=BC++)}function m(d,_){let v=0,g=0,M=0,E=0,R=0;const x=_.matrixWorldInverse;for(let y=0,T=d.length;y<T;y++){const U=d[y];if(U.isDirectionalLight){const P=r.directional[v];P.direction.setFromMatrixPosition(U.matrixWorld),l.setFromMatrixPosition(U.target.matrixWorld),P.direction.sub(l),P.direction.transformDirection(x),v++}else if(U.isSpotLight){const P=r.spot[M];P.position.setFromMatrixPosition(U.matrixWorld),P.position.applyMatrix4(x),P.direction.setFromMatrixPosition(U.matrixWorld),l.setFromMatrixPosition(U.target.matrixWorld),P.direction.sub(l),P.direction.transformDirection(x),M++}else if(U.isRectAreaLight){const P=r.rectArea[E];P.position.setFromMatrixPosition(U.matrixWorld),P.position.applyMatrix4(x),f.identity(),c.copy(U.matrixWorld),c.premultiply(x),f.extractRotation(c),P.halfWidth.set(U.width*.5,0,0),P.halfHeight.set(0,U.height*.5,0),P.halfWidth.applyMatrix4(f),P.halfHeight.applyMatrix4(f),E++}else if(U.isPointLight){const P=r.point[g];P.position.setFromMatrixPosition(U.matrixWorld),P.position.applyMatrix4(x),g++}else if(U.isHemisphereLight){const P=r.hemi[R];P.direction.setFromMatrixPosition(U.matrixWorld),P.direction.transformDirection(x),R++}}}return{setup:p,setupView:m,state:r}}function Rv(s){const e=new GC(s),i=[],r=[];function l(_){d.camera=_,i.length=0,r.length=0}function c(_){i.push(_)}function f(_){r.push(_)}function p(){e.setup(i)}function m(_){e.setupView(i,_)}const d={lightsArray:i,shadowsArray:r,camera:null,lights:e,transmissionRenderTarget:{}};return{init:l,state:d,setupLights:p,setupLightsView:m,pushLight:c,pushShadow:f}}function VC(s){let e=new WeakMap;function i(l,c=0){const f=e.get(l);let p;return f===void 0?(p=new Rv(s),e.set(l,[p])):c>=f.length?(p=new Rv(s),f.push(p)):p=f[c],p}function r(){e=new WeakMap}return{get:i,dispose:r}}const kC=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,jC=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ).rg;
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ).r;
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( max( 0.0, squared_mean - mean * mean ) );
	gl_FragColor = vec4( mean, std_dev, 0.0, 1.0 );
}`,XC=[new se(1,0,0),new se(-1,0,0),new se(0,1,0),new se(0,-1,0),new se(0,0,1),new se(0,0,-1)],WC=[new se(0,-1,0),new se(0,-1,0),new se(0,0,1),new se(0,0,-1),new se(0,-1,0),new se(0,-1,0)],Cv=new nn,el=new se,pd=new se;function qC(s,e,i){let r=new yx;const l=new mt,c=new mt,f=new rn,p=new oT,m=new lT,d={},_=i.maxTextureSize,v={[ds]:Zn,[Zn]:ds,[Sa]:Sa},g=new Ki({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new mt},radius:{value:4}},vertexShader:kC,fragmentShader:jC}),M=g.clone();M.defines.HORIZONTAL_PASS=1;const E=new Fi;E.setAttribute("position",new Yn(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));const R=new Na(E,g),x=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=au;let y=this.type;this.render=function(H,z,A){if(x.enabled===!1||x.autoUpdate===!1&&x.needsUpdate===!1||H.length===0)return;this.type===YE&&(st("WebGLShadowMap: PCFSoftShadowMap has been deprecated. Using PCFShadowMap instead."),this.type=au);const L=s.getRenderTarget(),pe=s.getActiveCubeFace(),w=s.getActiveMipmapLevel(),Y=s.state;Y.setBlending(ba),Y.buffers.depth.getReversed()===!0?Y.buffers.color.setClear(0,0,0,0):Y.buffers.color.setClear(1,1,1,1),Y.buffers.depth.setTest(!0),Y.setScissorTest(!1);const re=y!==this.type;re&&z.traverse(function(fe){fe.material&&(Array.isArray(fe.material)?fe.material.forEach(ee=>ee.needsUpdate=!0):fe.material.needsUpdate=!0)});for(let fe=0,ee=H.length;fe<ee;fe++){const I=H[fe],B=I.shadow;if(B===void 0){st("WebGLShadowMap:",I,"has no shadow.");continue}if(B.autoUpdate===!1&&B.needsUpdate===!1)continue;l.copy(B.mapSize);const $=B.getFrameExtents();l.multiply($),c.copy(B.mapSize),(l.x>_||l.y>_)&&(l.x>_&&(c.x=Math.floor(_/$.x),l.x=c.x*$.x,B.mapSize.x=c.x),l.y>_&&(c.y=Math.floor(_/$.y),l.y=c.y*$.y,B.mapSize.y=c.y));const Q=s.state.buffers.depth.getReversed();if(B.camera._reversedDepth=Q,B.map===null||re===!0){if(B.map!==null&&(B.map.depthTexture!==null&&(B.map.depthTexture.dispose(),B.map.depthTexture=null),B.map.dispose()),this.type===nl){if(I.isPointLight){st("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}B.map=new Yi(l.x,l.y,{format:Yr,type:Ca,minFilter:Nn,magFilter:Nn,generateMipmaps:!1}),B.map.texture.name=I.name+".shadowMap",B.map.depthTexture=new cl(l.x,l.y,Xi),B.map.depthTexture.name=I.name+".shadowMapDepth",B.map.depthTexture.format=wa,B.map.depthTexture.compareFunction=null,B.map.depthTexture.minFilter=Rn,B.map.depthTexture.magFilter=Rn}else I.isPointLight?(B.map=new Cx(l.x),B.map.depthTexture=new tT(l.x,Zi)):(B.map=new Yi(l.x,l.y),B.map.depthTexture=new cl(l.x,l.y,Zi)),B.map.depthTexture.name=I.name+".shadowMap",B.map.depthTexture.format=wa,this.type===au?(B.map.depthTexture.compareFunction=Q?wp:Cp,B.map.depthTexture.minFilter=Nn,B.map.depthTexture.magFilter=Nn):(B.map.depthTexture.compareFunction=null,B.map.depthTexture.minFilter=Rn,B.map.depthTexture.magFilter=Rn);B.camera.updateProjectionMatrix()}const de=B.map.isWebGLCubeRenderTarget?6:1;for(let O=0;O<de;O++){if(B.map.isWebGLCubeRenderTarget)s.setRenderTarget(B.map,O),s.clear();else{O===0&&(s.setRenderTarget(B.map),s.clear());const j=B.getViewport(O);f.set(c.x*j.x,c.y*j.y,c.x*j.z,c.y*j.w),Y.viewport(f)}if(I.isPointLight){const j=B.camera,ve=B.matrix,he=I.distance||j.far;he!==j.far&&(j.far=he,j.updateProjectionMatrix()),el.setFromMatrixPosition(I.matrixWorld),j.position.copy(el),pd.copy(j.position),pd.add(XC[O]),j.up.copy(WC[O]),j.lookAt(pd),j.updateMatrixWorld(),ve.makeTranslation(-el.x,-el.y,-el.z),Cv.multiplyMatrices(j.projectionMatrix,j.matrixWorldInverse),B._frustum.setFromProjectionMatrix(Cv,j.coordinateSystem,j.reversedDepth)}else B.updateMatrices(I);r=B.getFrustum(),P(z,A,B.camera,I,this.type)}B.isPointLightShadow!==!0&&this.type===nl&&T(B,A),B.needsUpdate=!1}y=this.type,x.needsUpdate=!1,s.setRenderTarget(L,pe,w)};function T(H,z){const A=e.update(R);g.defines.VSM_SAMPLES!==H.blurSamples&&(g.defines.VSM_SAMPLES=H.blurSamples,M.defines.VSM_SAMPLES=H.blurSamples,g.needsUpdate=!0,M.needsUpdate=!0),H.mapPass===null&&(H.mapPass=new Yi(l.x,l.y,{format:Yr,type:Ca})),g.uniforms.shadow_pass.value=H.map.depthTexture,g.uniforms.resolution.value=H.mapSize,g.uniforms.radius.value=H.radius,s.setRenderTarget(H.mapPass),s.clear(),s.renderBufferDirect(z,null,A,g,R,null),M.uniforms.shadow_pass.value=H.mapPass.texture,M.uniforms.resolution.value=H.mapSize,M.uniforms.radius.value=H.radius,s.setRenderTarget(H.map),s.clear(),s.renderBufferDirect(z,null,A,M,R,null)}function U(H,z,A,L){let pe=null;const w=A.isPointLight===!0?H.customDistanceMaterial:H.customDepthMaterial;if(w!==void 0)pe=w;else if(pe=A.isPointLight===!0?m:p,s.localClippingEnabled&&z.clipShadows===!0&&Array.isArray(z.clippingPlanes)&&z.clippingPlanes.length!==0||z.displacementMap&&z.displacementScale!==0||z.alphaMap&&z.alphaTest>0||z.map&&z.alphaTest>0||z.alphaToCoverage===!0){const Y=pe.uuid,re=z.uuid;let fe=d[Y];fe===void 0&&(fe={},d[Y]=fe);let ee=fe[re];ee===void 0&&(ee=pe.clone(),fe[re]=ee,z.addEventListener("dispose",V)),pe=ee}if(pe.visible=z.visible,pe.wireframe=z.wireframe,L===nl?pe.side=z.shadowSide!==null?z.shadowSide:z.side:pe.side=z.shadowSide!==null?z.shadowSide:v[z.side],pe.alphaMap=z.alphaMap,pe.alphaTest=z.alphaToCoverage===!0?.5:z.alphaTest,pe.map=z.map,pe.clipShadows=z.clipShadows,pe.clippingPlanes=z.clippingPlanes,pe.clipIntersection=z.clipIntersection,pe.displacementMap=z.displacementMap,pe.displacementScale=z.displacementScale,pe.displacementBias=z.displacementBias,pe.wireframeLinewidth=z.wireframeLinewidth,pe.linewidth=z.linewidth,A.isPointLight===!0&&pe.isMeshDistanceMaterial===!0){const Y=s.properties.get(pe);Y.light=A}return pe}function P(H,z,A,L,pe){if(H.visible===!1)return;if(H.layers.test(z.layers)&&(H.isMesh||H.isLine||H.isPoints)&&(H.castShadow||H.receiveShadow&&pe===nl)&&(!H.frustumCulled||r.intersectsObject(H))){H.modelViewMatrix.multiplyMatrices(A.matrixWorldInverse,H.matrixWorld);const re=e.update(H),fe=H.material;if(Array.isArray(fe)){const ee=re.groups;for(let I=0,B=ee.length;I<B;I++){const $=ee[I],Q=fe[$.materialIndex];if(Q&&Q.visible){const de=U(H,Q,L,pe);H.onBeforeShadow(s,H,z,A,re,de,$),s.renderBufferDirect(A,null,re,de,H,$),H.onAfterShadow(s,H,z,A,re,de,$)}}}else if(fe.visible){const ee=U(H,fe,L,pe);H.onBeforeShadow(s,H,z,A,re,ee,null),s.renderBufferDirect(A,null,re,ee,H,null),H.onAfterShadow(s,H,z,A,re,ee,null)}}const Y=H.children;for(let re=0,fe=Y.length;re<fe;re++)P(Y[re],z,A,L,pe)}function V(H){H.target.removeEventListener("dispose",V);for(const A in d){const L=d[A],pe=H.target.uuid;pe in L&&(L[pe].dispose(),delete L[pe])}}}function YC(s,e){function i(){let q=!1;const we=new rn;let Ce=null;const ze=new rn(0,0,0,0);return{setMask:function(Te){Ce!==Te&&!q&&(s.colorMask(Te,Te,Te,Te),Ce=Te)},setLocked:function(Te){q=Te},setClear:function(Te,me,He,it,Ft){Ft===!0&&(Te*=it,me*=it,He*=it),we.set(Te,me,He,it),ze.equals(we)===!1&&(s.clearColor(Te,me,He,it),ze.copy(we))},reset:function(){q=!1,Ce=null,ze.set(-1,0,0,0)}}}function r(){let q=!1,we=!1,Ce=null,ze=null,Te=null;return{setReversed:function(me){if(we!==me){const He=e.get("EXT_clip_control");me?He.clipControlEXT(He.LOWER_LEFT_EXT,He.ZERO_TO_ONE_EXT):He.clipControlEXT(He.LOWER_LEFT_EXT,He.NEGATIVE_ONE_TO_ONE_EXT),we=me;const it=Te;Te=null,this.setClear(it)}},getReversed:function(){return we},setTest:function(me){me?Se(s.DEPTH_TEST):Ae(s.DEPTH_TEST)},setMask:function(me){Ce!==me&&!q&&(s.depthMask(me),Ce=me)},setFunc:function(me){if(we&&(me=Cb[me]),ze!==me){switch(me){case Sd:s.depthFunc(s.NEVER);break;case Md:s.depthFunc(s.ALWAYS);break;case Ed:s.depthFunc(s.LESS);break;case Wr:s.depthFunc(s.LEQUAL);break;case bd:s.depthFunc(s.EQUAL);break;case Td:s.depthFunc(s.GEQUAL);break;case Ad:s.depthFunc(s.GREATER);break;case Rd:s.depthFunc(s.NOTEQUAL);break;default:s.depthFunc(s.LEQUAL)}ze=me}},setLocked:function(me){q=me},setClear:function(me){Te!==me&&(Te=me,we&&(me=1-me),s.clearDepth(me))},reset:function(){q=!1,Ce=null,ze=null,Te=null,we=!1}}}function l(){let q=!1,we=null,Ce=null,ze=null,Te=null,me=null,He=null,it=null,Ft=null;return{setTest:function(Tt){q||(Tt?Se(s.STENCIL_TEST):Ae(s.STENCIL_TEST))},setMask:function(Tt){we!==Tt&&!q&&(s.stencilMask(Tt),we=Tt)},setFunc:function(Tt,Ln,Mi){(Ce!==Tt||ze!==Ln||Te!==Mi)&&(s.stencilFunc(Tt,Ln,Mi),Ce=Tt,ze=Ln,Te=Mi)},setOp:function(Tt,Ln,Mi){(me!==Tt||He!==Ln||it!==Mi)&&(s.stencilOp(Tt,Ln,Mi),me=Tt,He=Ln,it=Mi)},setLocked:function(Tt){q=Tt},setClear:function(Tt){Ft!==Tt&&(s.clearStencil(Tt),Ft=Tt)},reset:function(){q=!1,we=null,Ce=null,ze=null,Te=null,me=null,He=null,it=null,Ft=null}}}const c=new i,f=new r,p=new l,m=new WeakMap,d=new WeakMap;let _={},v={},g=new WeakMap,M=[],E=null,R=!1,x=null,y=null,T=null,U=null,P=null,V=null,H=null,z=new Lt(0,0,0),A=0,L=!1,pe=null,w=null,Y=null,re=null,fe=null;const ee=s.getParameter(s.MAX_COMBINED_TEXTURE_IMAGE_UNITS);let I=!1,B=0;const $=s.getParameter(s.VERSION);$.indexOf("WebGL")!==-1?(B=parseFloat(/^WebGL (\d)/.exec($)[1]),I=B>=1):$.indexOf("OpenGL ES")!==-1&&(B=parseFloat(/^OpenGL ES (\d)/.exec($)[1]),I=B>=2);let Q=null,de={};const O=s.getParameter(s.SCISSOR_BOX),j=s.getParameter(s.VIEWPORT),ve=new rn().fromArray(O),he=new rn().fromArray(j);function Ne(q,we,Ce,ze){const Te=new Uint8Array(4),me=s.createTexture();s.bindTexture(q,me),s.texParameteri(q,s.TEXTURE_MIN_FILTER,s.NEAREST),s.texParameteri(q,s.TEXTURE_MAG_FILTER,s.NEAREST);for(let He=0;He<Ce;He++)q===s.TEXTURE_3D||q===s.TEXTURE_2D_ARRAY?s.texImage3D(we,0,s.RGBA,1,1,ze,0,s.RGBA,s.UNSIGNED_BYTE,Te):s.texImage2D(we+He,0,s.RGBA,1,1,0,s.RGBA,s.UNSIGNED_BYTE,Te);return me}const ie={};ie[s.TEXTURE_2D]=Ne(s.TEXTURE_2D,s.TEXTURE_2D,1),ie[s.TEXTURE_CUBE_MAP]=Ne(s.TEXTURE_CUBE_MAP,s.TEXTURE_CUBE_MAP_POSITIVE_X,6),ie[s.TEXTURE_2D_ARRAY]=Ne(s.TEXTURE_2D_ARRAY,s.TEXTURE_2D_ARRAY,1,1),ie[s.TEXTURE_3D]=Ne(s.TEXTURE_3D,s.TEXTURE_3D,1,1),c.setClear(0,0,0,1),f.setClear(1),p.setClear(0),Se(s.DEPTH_TEST),f.setFunc(Wr),lt(!1),Jt(w0),Se(s.CULL_FACE),gt(ba);function Se(q){_[q]!==!0&&(s.enable(q),_[q]=!0)}function Ae(q){_[q]!==!1&&(s.disable(q),_[q]=!1)}function Ge(q,we){return v[q]!==we?(s.bindFramebuffer(q,we),v[q]=we,q===s.DRAW_FRAMEBUFFER&&(v[s.FRAMEBUFFER]=we),q===s.FRAMEBUFFER&&(v[s.DRAW_FRAMEBUFFER]=we),!0):!1}function Qe(q,we){let Ce=M,ze=!1;if(q){Ce=g.get(we),Ce===void 0&&(Ce=[],g.set(we,Ce));const Te=q.textures;if(Ce.length!==Te.length||Ce[0]!==s.COLOR_ATTACHMENT0){for(let me=0,He=Te.length;me<He;me++)Ce[me]=s.COLOR_ATTACHMENT0+me;Ce.length=Te.length,ze=!0}}else Ce[0]!==s.BACK&&(Ce[0]=s.BACK,ze=!0);ze&&s.drawBuffers(Ce)}function qe(q){return E!==q?(s.useProgram(q),E=q,!0):!1}const $t={[Hs]:s.FUNC_ADD,[KE]:s.FUNC_SUBTRACT,[QE]:s.FUNC_REVERSE_SUBTRACT};$t[JE]=s.MIN,$t[$E]=s.MAX;const yt={[eb]:s.ZERO,[tb]:s.ONE,[nb]:s.SRC_COLOR,[xd]:s.SRC_ALPHA,[lb]:s.SRC_ALPHA_SATURATE,[rb]:s.DST_COLOR,[ab]:s.DST_ALPHA,[ib]:s.ONE_MINUS_SRC_COLOR,[yd]:s.ONE_MINUS_SRC_ALPHA,[ob]:s.ONE_MINUS_DST_COLOR,[sb]:s.ONE_MINUS_DST_ALPHA,[cb]:s.CONSTANT_COLOR,[ub]:s.ONE_MINUS_CONSTANT_COLOR,[fb]:s.CONSTANT_ALPHA,[hb]:s.ONE_MINUS_CONSTANT_ALPHA};function gt(q,we,Ce,ze,Te,me,He,it,Ft,Tt){if(q===ba){R===!0&&(Ae(s.BLEND),R=!1);return}if(R===!1&&(Se(s.BLEND),R=!0),q!==ZE){if(q!==x||Tt!==L){if((y!==Hs||P!==Hs)&&(s.blendEquation(s.FUNC_ADD),y=Hs,P=Hs),Tt)switch(q){case jr:s.blendFuncSeparate(s.ONE,s.ONE_MINUS_SRC_ALPHA,s.ONE,s.ONE_MINUS_SRC_ALPHA);break;case D0:s.blendFunc(s.ONE,s.ONE);break;case N0:s.blendFuncSeparate(s.ZERO,s.ONE_MINUS_SRC_COLOR,s.ZERO,s.ONE);break;case U0:s.blendFuncSeparate(s.DST_COLOR,s.ONE_MINUS_SRC_ALPHA,s.ZERO,s.ONE);break;default:At("WebGLState: Invalid blending: ",q);break}else switch(q){case jr:s.blendFuncSeparate(s.SRC_ALPHA,s.ONE_MINUS_SRC_ALPHA,s.ONE,s.ONE_MINUS_SRC_ALPHA);break;case D0:s.blendFuncSeparate(s.SRC_ALPHA,s.ONE,s.ONE,s.ONE);break;case N0:At("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case U0:At("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:At("WebGLState: Invalid blending: ",q);break}T=null,U=null,V=null,H=null,z.set(0,0,0),A=0,x=q,L=Tt}return}Te=Te||we,me=me||Ce,He=He||ze,(we!==y||Te!==P)&&(s.blendEquationSeparate($t[we],$t[Te]),y=we,P=Te),(Ce!==T||ze!==U||me!==V||He!==H)&&(s.blendFuncSeparate(yt[Ce],yt[ze],yt[me],yt[He]),T=Ce,U=ze,V=me,H=He),(it.equals(z)===!1||Ft!==A)&&(s.blendColor(it.r,it.g,it.b,Ft),z.copy(it),A=Ft),x=q,L=!1}function Nt(q,we){q.side===Sa?Ae(s.CULL_FACE):Se(s.CULL_FACE);let Ce=q.side===Zn;we&&(Ce=!Ce),lt(Ce),q.blending===jr&&q.transparent===!1?gt(ba):gt(q.blending,q.blendEquation,q.blendSrc,q.blendDst,q.blendEquationAlpha,q.blendSrcAlpha,q.blendDstAlpha,q.blendColor,q.blendAlpha,q.premultipliedAlpha),f.setFunc(q.depthFunc),f.setTest(q.depthTest),f.setMask(q.depthWrite),c.setMask(q.colorWrite);const ze=q.stencilWrite;p.setTest(ze),ze&&(p.setMask(q.stencilWriteMask),p.setFunc(q.stencilFunc,q.stencilRef,q.stencilFuncMask),p.setOp(q.stencilFail,q.stencilZFail,q.stencilZPass)),qt(q.polygonOffset,q.polygonOffsetFactor,q.polygonOffsetUnits),q.alphaToCoverage===!0?Se(s.SAMPLE_ALPHA_TO_COVERAGE):Ae(s.SAMPLE_ALPHA_TO_COVERAGE)}function lt(q){pe!==q&&(q?s.frontFace(s.CW):s.frontFace(s.CCW),pe=q)}function Jt(q){q!==WE?(Se(s.CULL_FACE),q!==w&&(q===w0?s.cullFace(s.BACK):q===qE?s.cullFace(s.FRONT):s.cullFace(s.FRONT_AND_BACK))):Ae(s.CULL_FACE),w=q}function k(q){q!==Y&&(I&&s.lineWidth(q),Y=q)}function qt(q,we,Ce){q?(Se(s.POLYGON_OFFSET_FILL),(re!==we||fe!==Ce)&&(re=we,fe=Ce,f.getReversed()&&(we=-we),s.polygonOffset(we,Ce))):Ae(s.POLYGON_OFFSET_FILL)}function bt(q){q?Se(s.SCISSOR_TEST):Ae(s.SCISSOR_TEST)}function Ot(q){q===void 0&&(q=s.TEXTURE0+ee-1),Q!==q&&(s.activeTexture(q),Q=q)}function Ye(q,we,Ce){Ce===void 0&&(Q===null?Ce=s.TEXTURE0+ee-1:Ce=Q);let ze=de[Ce];ze===void 0&&(ze={type:void 0,texture:void 0},de[Ce]=ze),(ze.type!==q||ze.texture!==we)&&(Q!==Ce&&(s.activeTexture(Ce),Q=Ce),s.bindTexture(q,we||ie[q]),ze.type=q,ze.texture=we)}function F(){const q=de[Q];q!==void 0&&q.type!==void 0&&(s.bindTexture(q.type,null),q.type=void 0,q.texture=void 0)}function b(){try{s.compressedTexImage2D(...arguments)}catch(q){At("WebGLState:",q)}}function Z(){try{s.compressedTexImage3D(...arguments)}catch(q){At("WebGLState:",q)}}function xe(){try{s.texSubImage2D(...arguments)}catch(q){At("WebGLState:",q)}}function Ee(){try{s.texSubImage3D(...arguments)}catch(q){At("WebGLState:",q)}}function ge(){try{s.compressedTexSubImage2D(...arguments)}catch(q){At("WebGLState:",q)}}function Xe(){try{s.compressedTexSubImage3D(...arguments)}catch(q){At("WebGLState:",q)}}function De(){try{s.texStorage2D(...arguments)}catch(q){At("WebGLState:",q)}}function Je(){try{s.texStorage3D(...arguments)}catch(q){At("WebGLState:",q)}}function tt(){try{s.texImage2D(...arguments)}catch(q){At("WebGLState:",q)}}function Re(){try{s.texImage3D(...arguments)}catch(q){At("WebGLState:",q)}}function be(q){ve.equals(q)===!1&&(s.scissor(q.x,q.y,q.z,q.w),ve.copy(q))}function Fe(q){he.equals(q)===!1&&(s.viewport(q.x,q.y,q.z,q.w),he.copy(q))}function Pe(q,we){let Ce=d.get(we);Ce===void 0&&(Ce=new WeakMap,d.set(we,Ce));let ze=Ce.get(q);ze===void 0&&(ze=s.getUniformBlockIndex(we,q.name),Ce.set(q,ze))}function Ie(q,we){const ze=d.get(we).get(q);m.get(we)!==ze&&(s.uniformBlockBinding(we,ze,q.__bindingPointIndex),m.set(we,ze))}function ut(){s.disable(s.BLEND),s.disable(s.CULL_FACE),s.disable(s.DEPTH_TEST),s.disable(s.POLYGON_OFFSET_FILL),s.disable(s.SCISSOR_TEST),s.disable(s.STENCIL_TEST),s.disable(s.SAMPLE_ALPHA_TO_COVERAGE),s.blendEquation(s.FUNC_ADD),s.blendFunc(s.ONE,s.ZERO),s.blendFuncSeparate(s.ONE,s.ZERO,s.ONE,s.ZERO),s.blendColor(0,0,0,0),s.colorMask(!0,!0,!0,!0),s.clearColor(0,0,0,0),s.depthMask(!0),s.depthFunc(s.LESS),f.setReversed(!1),s.clearDepth(1),s.stencilMask(4294967295),s.stencilFunc(s.ALWAYS,0,4294967295),s.stencilOp(s.KEEP,s.KEEP,s.KEEP),s.clearStencil(0),s.cullFace(s.BACK),s.frontFace(s.CCW),s.polygonOffset(0,0),s.activeTexture(s.TEXTURE0),s.bindFramebuffer(s.FRAMEBUFFER,null),s.bindFramebuffer(s.DRAW_FRAMEBUFFER,null),s.bindFramebuffer(s.READ_FRAMEBUFFER,null),s.useProgram(null),s.lineWidth(1),s.scissor(0,0,s.canvas.width,s.canvas.height),s.viewport(0,0,s.canvas.width,s.canvas.height),_={},Q=null,de={},v={},g=new WeakMap,M=[],E=null,R=!1,x=null,y=null,T=null,U=null,P=null,V=null,H=null,z=new Lt(0,0,0),A=0,L=!1,pe=null,w=null,Y=null,re=null,fe=null,ve.set(0,0,s.canvas.width,s.canvas.height),he.set(0,0,s.canvas.width,s.canvas.height),c.reset(),f.reset(),p.reset()}return{buffers:{color:c,depth:f,stencil:p},enable:Se,disable:Ae,bindFramebuffer:Ge,drawBuffers:Qe,useProgram:qe,setBlending:gt,setMaterial:Nt,setFlipSided:lt,setCullFace:Jt,setLineWidth:k,setPolygonOffset:qt,setScissorTest:bt,activeTexture:Ot,bindTexture:Ye,unbindTexture:F,compressedTexImage2D:b,compressedTexImage3D:Z,texImage2D:tt,texImage3D:Re,updateUBOMapping:Pe,uniformBlockBinding:Ie,texStorage2D:De,texStorage3D:Je,texSubImage2D:xe,texSubImage3D:Ee,compressedTexSubImage2D:ge,compressedTexSubImage3D:Xe,scissor:be,viewport:Fe,reset:ut}}function ZC(s,e,i,r,l,c,f){const p=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,m=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),d=new mt,_=new WeakMap;let v;const g=new WeakMap;let M=!1;try{M=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function E(F,b){return M?new OffscreenCanvas(F,b):pu("canvas")}function R(F,b,Z){let xe=1;const Ee=Ye(F);if((Ee.width>Z||Ee.height>Z)&&(xe=Z/Math.max(Ee.width,Ee.height)),xe<1)if(typeof HTMLImageElement<"u"&&F instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&F instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&F instanceof ImageBitmap||typeof VideoFrame<"u"&&F instanceof VideoFrame){const ge=Math.floor(xe*Ee.width),Xe=Math.floor(xe*Ee.height);v===void 0&&(v=E(ge,Xe));const De=b?E(ge,Xe):v;return De.width=ge,De.height=Xe,De.getContext("2d").drawImage(F,0,0,ge,Xe),st("WebGLRenderer: Texture has been resized from ("+Ee.width+"x"+Ee.height+") to ("+ge+"x"+Xe+")."),De}else return"data"in F&&st("WebGLRenderer: Image in DataTexture is too big ("+Ee.width+"x"+Ee.height+")."),F;return F}function x(F){return F.generateMipmaps}function y(F){s.generateMipmap(F)}function T(F){return F.isWebGLCubeRenderTarget?s.TEXTURE_CUBE_MAP:F.isWebGL3DRenderTarget?s.TEXTURE_3D:F.isWebGLArrayRenderTarget||F.isCompressedArrayTexture?s.TEXTURE_2D_ARRAY:s.TEXTURE_2D}function U(F,b,Z,xe,Ee=!1){if(F!==null){if(s[F]!==void 0)return s[F];st("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+F+"'")}let ge=b;if(b===s.RED&&(Z===s.FLOAT&&(ge=s.R32F),Z===s.HALF_FLOAT&&(ge=s.R16F),Z===s.UNSIGNED_BYTE&&(ge=s.R8)),b===s.RED_INTEGER&&(Z===s.UNSIGNED_BYTE&&(ge=s.R8UI),Z===s.UNSIGNED_SHORT&&(ge=s.R16UI),Z===s.UNSIGNED_INT&&(ge=s.R32UI),Z===s.BYTE&&(ge=s.R8I),Z===s.SHORT&&(ge=s.R16I),Z===s.INT&&(ge=s.R32I)),b===s.RG&&(Z===s.FLOAT&&(ge=s.RG32F),Z===s.HALF_FLOAT&&(ge=s.RG16F),Z===s.UNSIGNED_BYTE&&(ge=s.RG8)),b===s.RG_INTEGER&&(Z===s.UNSIGNED_BYTE&&(ge=s.RG8UI),Z===s.UNSIGNED_SHORT&&(ge=s.RG16UI),Z===s.UNSIGNED_INT&&(ge=s.RG32UI),Z===s.BYTE&&(ge=s.RG8I),Z===s.SHORT&&(ge=s.RG16I),Z===s.INT&&(ge=s.RG32I)),b===s.RGB_INTEGER&&(Z===s.UNSIGNED_BYTE&&(ge=s.RGB8UI),Z===s.UNSIGNED_SHORT&&(ge=s.RGB16UI),Z===s.UNSIGNED_INT&&(ge=s.RGB32UI),Z===s.BYTE&&(ge=s.RGB8I),Z===s.SHORT&&(ge=s.RGB16I),Z===s.INT&&(ge=s.RGB32I)),b===s.RGBA_INTEGER&&(Z===s.UNSIGNED_BYTE&&(ge=s.RGBA8UI),Z===s.UNSIGNED_SHORT&&(ge=s.RGBA16UI),Z===s.UNSIGNED_INT&&(ge=s.RGBA32UI),Z===s.BYTE&&(ge=s.RGBA8I),Z===s.SHORT&&(ge=s.RGBA16I),Z===s.INT&&(ge=s.RGBA32I)),b===s.RGB&&(Z===s.UNSIGNED_INT_5_9_9_9_REV&&(ge=s.RGB9_E5),Z===s.UNSIGNED_INT_10F_11F_11F_REV&&(ge=s.R11F_G11F_B10F)),b===s.RGBA){const Xe=Ee?hu:Rt.getTransfer(xe);Z===s.FLOAT&&(ge=s.RGBA32F),Z===s.HALF_FLOAT&&(ge=s.RGBA16F),Z===s.UNSIGNED_BYTE&&(ge=Xe===Bt?s.SRGB8_ALPHA8:s.RGBA8),Z===s.UNSIGNED_SHORT_4_4_4_4&&(ge=s.RGBA4),Z===s.UNSIGNED_SHORT_5_5_5_1&&(ge=s.RGB5_A1)}return(ge===s.R16F||ge===s.R32F||ge===s.RG16F||ge===s.RG32F||ge===s.RGBA16F||ge===s.RGBA32F)&&e.get("EXT_color_buffer_float"),ge}function P(F,b){let Z;return F?b===null||b===Zi||b===ll?Z=s.DEPTH24_STENCIL8:b===Xi?Z=s.DEPTH32F_STENCIL8:b===ol&&(Z=s.DEPTH24_STENCIL8,st("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):b===null||b===Zi||b===ll?Z=s.DEPTH_COMPONENT24:b===Xi?Z=s.DEPTH_COMPONENT32F:b===ol&&(Z=s.DEPTH_COMPONENT16),Z}function V(F,b){return x(F)===!0||F.isFramebufferTexture&&F.minFilter!==Rn&&F.minFilter!==Nn?Math.log2(Math.max(b.width,b.height))+1:F.mipmaps!==void 0&&F.mipmaps.length>0?F.mipmaps.length:F.isCompressedTexture&&Array.isArray(F.image)?b.mipmaps.length:1}function H(F){const b=F.target;b.removeEventListener("dispose",H),A(b),b.isVideoTexture&&_.delete(b)}function z(F){const b=F.target;b.removeEventListener("dispose",z),pe(b)}function A(F){const b=r.get(F);if(b.__webglInit===void 0)return;const Z=F.source,xe=g.get(Z);if(xe){const Ee=xe[b.__cacheKey];Ee.usedTimes--,Ee.usedTimes===0&&L(F),Object.keys(xe).length===0&&g.delete(Z)}r.remove(F)}function L(F){const b=r.get(F);s.deleteTexture(b.__webglTexture);const Z=F.source,xe=g.get(Z);delete xe[b.__cacheKey],f.memory.textures--}function pe(F){const b=r.get(F);if(F.depthTexture&&(F.depthTexture.dispose(),r.remove(F.depthTexture)),F.isWebGLCubeRenderTarget)for(let xe=0;xe<6;xe++){if(Array.isArray(b.__webglFramebuffer[xe]))for(let Ee=0;Ee<b.__webglFramebuffer[xe].length;Ee++)s.deleteFramebuffer(b.__webglFramebuffer[xe][Ee]);else s.deleteFramebuffer(b.__webglFramebuffer[xe]);b.__webglDepthbuffer&&s.deleteRenderbuffer(b.__webglDepthbuffer[xe])}else{if(Array.isArray(b.__webglFramebuffer))for(let xe=0;xe<b.__webglFramebuffer.length;xe++)s.deleteFramebuffer(b.__webglFramebuffer[xe]);else s.deleteFramebuffer(b.__webglFramebuffer);if(b.__webglDepthbuffer&&s.deleteRenderbuffer(b.__webglDepthbuffer),b.__webglMultisampledFramebuffer&&s.deleteFramebuffer(b.__webglMultisampledFramebuffer),b.__webglColorRenderbuffer)for(let xe=0;xe<b.__webglColorRenderbuffer.length;xe++)b.__webglColorRenderbuffer[xe]&&s.deleteRenderbuffer(b.__webglColorRenderbuffer[xe]);b.__webglDepthRenderbuffer&&s.deleteRenderbuffer(b.__webglDepthRenderbuffer)}const Z=F.textures;for(let xe=0,Ee=Z.length;xe<Ee;xe++){const ge=r.get(Z[xe]);ge.__webglTexture&&(s.deleteTexture(ge.__webglTexture),f.memory.textures--),r.remove(Z[xe])}r.remove(F)}let w=0;function Y(){w=0}function re(){const F=w;return F>=l.maxTextures&&st("WebGLTextures: Trying to use "+F+" texture units while this GPU supports only "+l.maxTextures),w+=1,F}function fe(F){const b=[];return b.push(F.wrapS),b.push(F.wrapT),b.push(F.wrapR||0),b.push(F.magFilter),b.push(F.minFilter),b.push(F.anisotropy),b.push(F.internalFormat),b.push(F.format),b.push(F.type),b.push(F.generateMipmaps),b.push(F.premultiplyAlpha),b.push(F.flipY),b.push(F.unpackAlignment),b.push(F.colorSpace),b.join()}function ee(F,b){const Z=r.get(F);if(F.isVideoTexture&&bt(F),F.isRenderTargetTexture===!1&&F.isExternalTexture!==!0&&F.version>0&&Z.__version!==F.version){const xe=F.image;if(xe===null)st("WebGLRenderer: Texture marked for update but no image data found.");else if(xe.complete===!1)st("WebGLRenderer: Texture marked for update but image is incomplete");else{ie(Z,F,b);return}}else F.isExternalTexture&&(Z.__webglTexture=F.sourceTexture?F.sourceTexture:null);i.bindTexture(s.TEXTURE_2D,Z.__webglTexture,s.TEXTURE0+b)}function I(F,b){const Z=r.get(F);if(F.isRenderTargetTexture===!1&&F.version>0&&Z.__version!==F.version){ie(Z,F,b);return}else F.isExternalTexture&&(Z.__webglTexture=F.sourceTexture?F.sourceTexture:null);i.bindTexture(s.TEXTURE_2D_ARRAY,Z.__webglTexture,s.TEXTURE0+b)}function B(F,b){const Z=r.get(F);if(F.isRenderTargetTexture===!1&&F.version>0&&Z.__version!==F.version){ie(Z,F,b);return}i.bindTexture(s.TEXTURE_3D,Z.__webglTexture,s.TEXTURE0+b)}function $(F,b){const Z=r.get(F);if(F.isCubeDepthTexture!==!0&&F.version>0&&Z.__version!==F.version){Se(Z,F,b);return}i.bindTexture(s.TEXTURE_CUBE_MAP,Z.__webglTexture,s.TEXTURE0+b)}const Q={[Cd]:s.REPEAT,[Ma]:s.CLAMP_TO_EDGE,[wd]:s.MIRRORED_REPEAT},de={[Rn]:s.NEAREST,[mb]:s.NEAREST_MIPMAP_NEAREST,[Dc]:s.NEAREST_MIPMAP_LINEAR,[Nn]:s.LINEAR,[Bh]:s.LINEAR_MIPMAP_NEAREST,[Vs]:s.LINEAR_MIPMAP_LINEAR},O={[xb]:s.NEVER,[bb]:s.ALWAYS,[yb]:s.LESS,[Cp]:s.LEQUAL,[Sb]:s.EQUAL,[wp]:s.GEQUAL,[Mb]:s.GREATER,[Eb]:s.NOTEQUAL};function j(F,b){if(b.type===Xi&&e.has("OES_texture_float_linear")===!1&&(b.magFilter===Nn||b.magFilter===Bh||b.magFilter===Dc||b.magFilter===Vs||b.minFilter===Nn||b.minFilter===Bh||b.minFilter===Dc||b.minFilter===Vs)&&st("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),s.texParameteri(F,s.TEXTURE_WRAP_S,Q[b.wrapS]),s.texParameteri(F,s.TEXTURE_WRAP_T,Q[b.wrapT]),(F===s.TEXTURE_3D||F===s.TEXTURE_2D_ARRAY)&&s.texParameteri(F,s.TEXTURE_WRAP_R,Q[b.wrapR]),s.texParameteri(F,s.TEXTURE_MAG_FILTER,de[b.magFilter]),s.texParameteri(F,s.TEXTURE_MIN_FILTER,de[b.minFilter]),b.compareFunction&&(s.texParameteri(F,s.TEXTURE_COMPARE_MODE,s.COMPARE_REF_TO_TEXTURE),s.texParameteri(F,s.TEXTURE_COMPARE_FUNC,O[b.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(b.magFilter===Rn||b.minFilter!==Dc&&b.minFilter!==Vs||b.type===Xi&&e.has("OES_texture_float_linear")===!1)return;if(b.anisotropy>1||r.get(b).__currentAnisotropy){const Z=e.get("EXT_texture_filter_anisotropic");s.texParameterf(F,Z.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(b.anisotropy,l.getMaxAnisotropy())),r.get(b).__currentAnisotropy=b.anisotropy}}}function ve(F,b){let Z=!1;F.__webglInit===void 0&&(F.__webglInit=!0,b.addEventListener("dispose",H));const xe=b.source;let Ee=g.get(xe);Ee===void 0&&(Ee={},g.set(xe,Ee));const ge=fe(b);if(ge!==F.__cacheKey){Ee[ge]===void 0&&(Ee[ge]={texture:s.createTexture(),usedTimes:0},f.memory.textures++,Z=!0),Ee[ge].usedTimes++;const Xe=Ee[F.__cacheKey];Xe!==void 0&&(Ee[F.__cacheKey].usedTimes--,Xe.usedTimes===0&&L(b)),F.__cacheKey=ge,F.__webglTexture=Ee[ge].texture}return Z}function he(F,b,Z){return Math.floor(Math.floor(F/Z)/b)}function Ne(F,b,Z,xe){const ge=F.updateRanges;if(ge.length===0)i.texSubImage2D(s.TEXTURE_2D,0,0,0,b.width,b.height,Z,xe,b.data);else{ge.sort((Re,be)=>Re.start-be.start);let Xe=0;for(let Re=1;Re<ge.length;Re++){const be=ge[Xe],Fe=ge[Re],Pe=be.start+be.count,Ie=he(Fe.start,b.width,4),ut=he(be.start,b.width,4);Fe.start<=Pe+1&&Ie===ut&&he(Fe.start+Fe.count-1,b.width,4)===Ie?be.count=Math.max(be.count,Fe.start+Fe.count-be.start):(++Xe,ge[Xe]=Fe)}ge.length=Xe+1;const De=s.getParameter(s.UNPACK_ROW_LENGTH),Je=s.getParameter(s.UNPACK_SKIP_PIXELS),tt=s.getParameter(s.UNPACK_SKIP_ROWS);s.pixelStorei(s.UNPACK_ROW_LENGTH,b.width);for(let Re=0,be=ge.length;Re<be;Re++){const Fe=ge[Re],Pe=Math.floor(Fe.start/4),Ie=Math.ceil(Fe.count/4),ut=Pe%b.width,q=Math.floor(Pe/b.width),we=Ie,Ce=1;s.pixelStorei(s.UNPACK_SKIP_PIXELS,ut),s.pixelStorei(s.UNPACK_SKIP_ROWS,q),i.texSubImage2D(s.TEXTURE_2D,0,ut,q,we,Ce,Z,xe,b.data)}F.clearUpdateRanges(),s.pixelStorei(s.UNPACK_ROW_LENGTH,De),s.pixelStorei(s.UNPACK_SKIP_PIXELS,Je),s.pixelStorei(s.UNPACK_SKIP_ROWS,tt)}}function ie(F,b,Z){let xe=s.TEXTURE_2D;(b.isDataArrayTexture||b.isCompressedArrayTexture)&&(xe=s.TEXTURE_2D_ARRAY),b.isData3DTexture&&(xe=s.TEXTURE_3D);const Ee=ve(F,b),ge=b.source;i.bindTexture(xe,F.__webglTexture,s.TEXTURE0+Z);const Xe=r.get(ge);if(ge.version!==Xe.__version||Ee===!0){i.activeTexture(s.TEXTURE0+Z);const De=Rt.getPrimaries(Rt.workingColorSpace),Je=b.colorSpace===fs?null:Rt.getPrimaries(b.colorSpace),tt=b.colorSpace===fs||De===Je?s.NONE:s.BROWSER_DEFAULT_WEBGL;s.pixelStorei(s.UNPACK_FLIP_Y_WEBGL,b.flipY),s.pixelStorei(s.UNPACK_PREMULTIPLY_ALPHA_WEBGL,b.premultiplyAlpha),s.pixelStorei(s.UNPACK_ALIGNMENT,b.unpackAlignment),s.pixelStorei(s.UNPACK_COLORSPACE_CONVERSION_WEBGL,tt);let Re=R(b.image,!1,l.maxTextureSize);Re=Ot(b,Re);const be=c.convert(b.format,b.colorSpace),Fe=c.convert(b.type);let Pe=U(b.internalFormat,be,Fe,b.colorSpace,b.isVideoTexture);j(xe,b);let Ie;const ut=b.mipmaps,q=b.isVideoTexture!==!0,we=Xe.__version===void 0||Ee===!0,Ce=ge.dataReady,ze=V(b,Re);if(b.isDepthTexture)Pe=P(b.format===ks,b.type),we&&(q?i.texStorage2D(s.TEXTURE_2D,1,Pe,Re.width,Re.height):i.texImage2D(s.TEXTURE_2D,0,Pe,Re.width,Re.height,0,be,Fe,null));else if(b.isDataTexture)if(ut.length>0){q&&we&&i.texStorage2D(s.TEXTURE_2D,ze,Pe,ut[0].width,ut[0].height);for(let Te=0,me=ut.length;Te<me;Te++)Ie=ut[Te],q?Ce&&i.texSubImage2D(s.TEXTURE_2D,Te,0,0,Ie.width,Ie.height,be,Fe,Ie.data):i.texImage2D(s.TEXTURE_2D,Te,Pe,Ie.width,Ie.height,0,be,Fe,Ie.data);b.generateMipmaps=!1}else q?(we&&i.texStorage2D(s.TEXTURE_2D,ze,Pe,Re.width,Re.height),Ce&&Ne(b,Re,be,Fe)):i.texImage2D(s.TEXTURE_2D,0,Pe,Re.width,Re.height,0,be,Fe,Re.data);else if(b.isCompressedTexture)if(b.isCompressedArrayTexture){q&&we&&i.texStorage3D(s.TEXTURE_2D_ARRAY,ze,Pe,ut[0].width,ut[0].height,Re.depth);for(let Te=0,me=ut.length;Te<me;Te++)if(Ie=ut[Te],b.format!==Li)if(be!==null)if(q){if(Ce)if(b.layerUpdates.size>0){const He=sv(Ie.width,Ie.height,b.format,b.type);for(const it of b.layerUpdates){const Ft=Ie.data.subarray(it*He/Ie.data.BYTES_PER_ELEMENT,(it+1)*He/Ie.data.BYTES_PER_ELEMENT);i.compressedTexSubImage3D(s.TEXTURE_2D_ARRAY,Te,0,0,it,Ie.width,Ie.height,1,be,Ft)}b.clearLayerUpdates()}else i.compressedTexSubImage3D(s.TEXTURE_2D_ARRAY,Te,0,0,0,Ie.width,Ie.height,Re.depth,be,Ie.data)}else i.compressedTexImage3D(s.TEXTURE_2D_ARRAY,Te,Pe,Ie.width,Ie.height,Re.depth,0,Ie.data,0,0);else st("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else q?Ce&&i.texSubImage3D(s.TEXTURE_2D_ARRAY,Te,0,0,0,Ie.width,Ie.height,Re.depth,be,Fe,Ie.data):i.texImage3D(s.TEXTURE_2D_ARRAY,Te,Pe,Ie.width,Ie.height,Re.depth,0,be,Fe,Ie.data)}else{q&&we&&i.texStorage2D(s.TEXTURE_2D,ze,Pe,ut[0].width,ut[0].height);for(let Te=0,me=ut.length;Te<me;Te++)Ie=ut[Te],b.format!==Li?be!==null?q?Ce&&i.compressedTexSubImage2D(s.TEXTURE_2D,Te,0,0,Ie.width,Ie.height,be,Ie.data):i.compressedTexImage2D(s.TEXTURE_2D,Te,Pe,Ie.width,Ie.height,0,Ie.data):st("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):q?Ce&&i.texSubImage2D(s.TEXTURE_2D,Te,0,0,Ie.width,Ie.height,be,Fe,Ie.data):i.texImage2D(s.TEXTURE_2D,Te,Pe,Ie.width,Ie.height,0,be,Fe,Ie.data)}else if(b.isDataArrayTexture)if(q){if(we&&i.texStorage3D(s.TEXTURE_2D_ARRAY,ze,Pe,Re.width,Re.height,Re.depth),Ce)if(b.layerUpdates.size>0){const Te=sv(Re.width,Re.height,b.format,b.type);for(const me of b.layerUpdates){const He=Re.data.subarray(me*Te/Re.data.BYTES_PER_ELEMENT,(me+1)*Te/Re.data.BYTES_PER_ELEMENT);i.texSubImage3D(s.TEXTURE_2D_ARRAY,0,0,0,me,Re.width,Re.height,1,be,Fe,He)}b.clearLayerUpdates()}else i.texSubImage3D(s.TEXTURE_2D_ARRAY,0,0,0,0,Re.width,Re.height,Re.depth,be,Fe,Re.data)}else i.texImage3D(s.TEXTURE_2D_ARRAY,0,Pe,Re.width,Re.height,Re.depth,0,be,Fe,Re.data);else if(b.isData3DTexture)q?(we&&i.texStorage3D(s.TEXTURE_3D,ze,Pe,Re.width,Re.height,Re.depth),Ce&&i.texSubImage3D(s.TEXTURE_3D,0,0,0,0,Re.width,Re.height,Re.depth,be,Fe,Re.data)):i.texImage3D(s.TEXTURE_3D,0,Pe,Re.width,Re.height,Re.depth,0,be,Fe,Re.data);else if(b.isFramebufferTexture){if(we)if(q)i.texStorage2D(s.TEXTURE_2D,ze,Pe,Re.width,Re.height);else{let Te=Re.width,me=Re.height;for(let He=0;He<ze;He++)i.texImage2D(s.TEXTURE_2D,He,Pe,Te,me,0,be,Fe,null),Te>>=1,me>>=1}}else if(ut.length>0){if(q&&we){const Te=Ye(ut[0]);i.texStorage2D(s.TEXTURE_2D,ze,Pe,Te.width,Te.height)}for(let Te=0,me=ut.length;Te<me;Te++)Ie=ut[Te],q?Ce&&i.texSubImage2D(s.TEXTURE_2D,Te,0,0,be,Fe,Ie):i.texImage2D(s.TEXTURE_2D,Te,Pe,be,Fe,Ie);b.generateMipmaps=!1}else if(q){if(we){const Te=Ye(Re);i.texStorage2D(s.TEXTURE_2D,ze,Pe,Te.width,Te.height)}Ce&&i.texSubImage2D(s.TEXTURE_2D,0,0,0,be,Fe,Re)}else i.texImage2D(s.TEXTURE_2D,0,Pe,be,Fe,Re);x(b)&&y(xe),Xe.__version=ge.version,b.onUpdate&&b.onUpdate(b)}F.__version=b.version}function Se(F,b,Z){if(b.image.length!==6)return;const xe=ve(F,b),Ee=b.source;i.bindTexture(s.TEXTURE_CUBE_MAP,F.__webglTexture,s.TEXTURE0+Z);const ge=r.get(Ee);if(Ee.version!==ge.__version||xe===!0){i.activeTexture(s.TEXTURE0+Z);const Xe=Rt.getPrimaries(Rt.workingColorSpace),De=b.colorSpace===fs?null:Rt.getPrimaries(b.colorSpace),Je=b.colorSpace===fs||Xe===De?s.NONE:s.BROWSER_DEFAULT_WEBGL;s.pixelStorei(s.UNPACK_FLIP_Y_WEBGL,b.flipY),s.pixelStorei(s.UNPACK_PREMULTIPLY_ALPHA_WEBGL,b.premultiplyAlpha),s.pixelStorei(s.UNPACK_ALIGNMENT,b.unpackAlignment),s.pixelStorei(s.UNPACK_COLORSPACE_CONVERSION_WEBGL,Je);const tt=b.isCompressedTexture||b.image[0].isCompressedTexture,Re=b.image[0]&&b.image[0].isDataTexture,be=[];for(let me=0;me<6;me++)!tt&&!Re?be[me]=R(b.image[me],!0,l.maxCubemapSize):be[me]=Re?b.image[me].image:b.image[me],be[me]=Ot(b,be[me]);const Fe=be[0],Pe=c.convert(b.format,b.colorSpace),Ie=c.convert(b.type),ut=U(b.internalFormat,Pe,Ie,b.colorSpace),q=b.isVideoTexture!==!0,we=ge.__version===void 0||xe===!0,Ce=Ee.dataReady;let ze=V(b,Fe);j(s.TEXTURE_CUBE_MAP,b);let Te;if(tt){q&&we&&i.texStorage2D(s.TEXTURE_CUBE_MAP,ze,ut,Fe.width,Fe.height);for(let me=0;me<6;me++){Te=be[me].mipmaps;for(let He=0;He<Te.length;He++){const it=Te[He];b.format!==Li?Pe!==null?q?Ce&&i.compressedTexSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,He,0,0,it.width,it.height,Pe,it.data):i.compressedTexImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,He,ut,it.width,it.height,0,it.data):st("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):q?Ce&&i.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,He,0,0,it.width,it.height,Pe,Ie,it.data):i.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,He,ut,it.width,it.height,0,Pe,Ie,it.data)}}}else{if(Te=b.mipmaps,q&&we){Te.length>0&&ze++;const me=Ye(be[0]);i.texStorage2D(s.TEXTURE_CUBE_MAP,ze,ut,me.width,me.height)}for(let me=0;me<6;me++)if(Re){q?Ce&&i.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,0,0,0,be[me].width,be[me].height,Pe,Ie,be[me].data):i.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,0,ut,be[me].width,be[me].height,0,Pe,Ie,be[me].data);for(let He=0;He<Te.length;He++){const Ft=Te[He].image[me].image;q?Ce&&i.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,He+1,0,0,Ft.width,Ft.height,Pe,Ie,Ft.data):i.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,He+1,ut,Ft.width,Ft.height,0,Pe,Ie,Ft.data)}}else{q?Ce&&i.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,0,0,0,Pe,Ie,be[me]):i.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,0,ut,Pe,Ie,be[me]);for(let He=0;He<Te.length;He++){const it=Te[He];q?Ce&&i.texSubImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,He+1,0,0,Pe,Ie,it.image[me]):i.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+me,He+1,ut,Pe,Ie,it.image[me])}}}x(b)&&y(s.TEXTURE_CUBE_MAP),ge.__version=Ee.version,b.onUpdate&&b.onUpdate(b)}F.__version=b.version}function Ae(F,b,Z,xe,Ee,ge){const Xe=c.convert(Z.format,Z.colorSpace),De=c.convert(Z.type),Je=U(Z.internalFormat,Xe,De,Z.colorSpace),tt=r.get(b),Re=r.get(Z);if(Re.__renderTarget=b,!tt.__hasExternalTextures){const be=Math.max(1,b.width>>ge),Fe=Math.max(1,b.height>>ge);Ee===s.TEXTURE_3D||Ee===s.TEXTURE_2D_ARRAY?i.texImage3D(Ee,ge,Je,be,Fe,b.depth,0,Xe,De,null):i.texImage2D(Ee,ge,Je,be,Fe,0,Xe,De,null)}i.bindFramebuffer(s.FRAMEBUFFER,F),qt(b)?p.framebufferTexture2DMultisampleEXT(s.FRAMEBUFFER,xe,Ee,Re.__webglTexture,0,k(b)):(Ee===s.TEXTURE_2D||Ee>=s.TEXTURE_CUBE_MAP_POSITIVE_X&&Ee<=s.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&s.framebufferTexture2D(s.FRAMEBUFFER,xe,Ee,Re.__webglTexture,ge),i.bindFramebuffer(s.FRAMEBUFFER,null)}function Ge(F,b,Z){if(s.bindRenderbuffer(s.RENDERBUFFER,F),b.depthBuffer){const xe=b.depthTexture,Ee=xe&&xe.isDepthTexture?xe.type:null,ge=P(b.stencilBuffer,Ee),Xe=b.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT;qt(b)?p.renderbufferStorageMultisampleEXT(s.RENDERBUFFER,k(b),ge,b.width,b.height):Z?s.renderbufferStorageMultisample(s.RENDERBUFFER,k(b),ge,b.width,b.height):s.renderbufferStorage(s.RENDERBUFFER,ge,b.width,b.height),s.framebufferRenderbuffer(s.FRAMEBUFFER,Xe,s.RENDERBUFFER,F)}else{const xe=b.textures;for(let Ee=0;Ee<xe.length;Ee++){const ge=xe[Ee],Xe=c.convert(ge.format,ge.colorSpace),De=c.convert(ge.type),Je=U(ge.internalFormat,Xe,De,ge.colorSpace);qt(b)?p.renderbufferStorageMultisampleEXT(s.RENDERBUFFER,k(b),Je,b.width,b.height):Z?s.renderbufferStorageMultisample(s.RENDERBUFFER,k(b),Je,b.width,b.height):s.renderbufferStorage(s.RENDERBUFFER,Je,b.width,b.height)}}s.bindRenderbuffer(s.RENDERBUFFER,null)}function Qe(F,b,Z){const xe=b.isWebGLCubeRenderTarget===!0;if(i.bindFramebuffer(s.FRAMEBUFFER,F),!(b.depthTexture&&b.depthTexture.isDepthTexture))throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");const Ee=r.get(b.depthTexture);if(Ee.__renderTarget=b,(!Ee.__webglTexture||b.depthTexture.image.width!==b.width||b.depthTexture.image.height!==b.height)&&(b.depthTexture.image.width=b.width,b.depthTexture.image.height=b.height,b.depthTexture.needsUpdate=!0),xe){if(Ee.__webglInit===void 0&&(Ee.__webglInit=!0,b.depthTexture.addEventListener("dispose",H)),Ee.__webglTexture===void 0){Ee.__webglTexture=s.createTexture(),i.bindTexture(s.TEXTURE_CUBE_MAP,Ee.__webglTexture),j(s.TEXTURE_CUBE_MAP,b.depthTexture);const tt=c.convert(b.depthTexture.format),Re=c.convert(b.depthTexture.type);let be;b.depthTexture.format===wa?be=s.DEPTH_COMPONENT24:b.depthTexture.format===ks&&(be=s.DEPTH24_STENCIL8);for(let Fe=0;Fe<6;Fe++)s.texImage2D(s.TEXTURE_CUBE_MAP_POSITIVE_X+Fe,0,be,b.width,b.height,0,tt,Re,null)}}else ee(b.depthTexture,0);const ge=Ee.__webglTexture,Xe=k(b),De=xe?s.TEXTURE_CUBE_MAP_POSITIVE_X+Z:s.TEXTURE_2D,Je=b.depthTexture.format===ks?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT;if(b.depthTexture.format===wa)qt(b)?p.framebufferTexture2DMultisampleEXT(s.FRAMEBUFFER,Je,De,ge,0,Xe):s.framebufferTexture2D(s.FRAMEBUFFER,Je,De,ge,0);else if(b.depthTexture.format===ks)qt(b)?p.framebufferTexture2DMultisampleEXT(s.FRAMEBUFFER,Je,De,ge,0,Xe):s.framebufferTexture2D(s.FRAMEBUFFER,Je,De,ge,0);else throw new Error("Unknown depthTexture format")}function qe(F){const b=r.get(F),Z=F.isWebGLCubeRenderTarget===!0;if(b.__boundDepthTexture!==F.depthTexture){const xe=F.depthTexture;if(b.__depthDisposeCallback&&b.__depthDisposeCallback(),xe){const Ee=()=>{delete b.__boundDepthTexture,delete b.__depthDisposeCallback,xe.removeEventListener("dispose",Ee)};xe.addEventListener("dispose",Ee),b.__depthDisposeCallback=Ee}b.__boundDepthTexture=xe}if(F.depthTexture&&!b.__autoAllocateDepthBuffer)if(Z)for(let xe=0;xe<6;xe++)Qe(b.__webglFramebuffer[xe],F,xe);else{const xe=F.texture.mipmaps;xe&&xe.length>0?Qe(b.__webglFramebuffer[0],F,0):Qe(b.__webglFramebuffer,F,0)}else if(Z){b.__webglDepthbuffer=[];for(let xe=0;xe<6;xe++)if(i.bindFramebuffer(s.FRAMEBUFFER,b.__webglFramebuffer[xe]),b.__webglDepthbuffer[xe]===void 0)b.__webglDepthbuffer[xe]=s.createRenderbuffer(),Ge(b.__webglDepthbuffer[xe],F,!1);else{const Ee=F.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT,ge=b.__webglDepthbuffer[xe];s.bindRenderbuffer(s.RENDERBUFFER,ge),s.framebufferRenderbuffer(s.FRAMEBUFFER,Ee,s.RENDERBUFFER,ge)}}else{const xe=F.texture.mipmaps;if(xe&&xe.length>0?i.bindFramebuffer(s.FRAMEBUFFER,b.__webglFramebuffer[0]):i.bindFramebuffer(s.FRAMEBUFFER,b.__webglFramebuffer),b.__webglDepthbuffer===void 0)b.__webglDepthbuffer=s.createRenderbuffer(),Ge(b.__webglDepthbuffer,F,!1);else{const Ee=F.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT,ge=b.__webglDepthbuffer;s.bindRenderbuffer(s.RENDERBUFFER,ge),s.framebufferRenderbuffer(s.FRAMEBUFFER,Ee,s.RENDERBUFFER,ge)}}i.bindFramebuffer(s.FRAMEBUFFER,null)}function $t(F,b,Z){const xe=r.get(F);b!==void 0&&Ae(xe.__webglFramebuffer,F,F.texture,s.COLOR_ATTACHMENT0,s.TEXTURE_2D,0),Z!==void 0&&qe(F)}function yt(F){const b=F.texture,Z=r.get(F),xe=r.get(b);F.addEventListener("dispose",z);const Ee=F.textures,ge=F.isWebGLCubeRenderTarget===!0,Xe=Ee.length>1;if(Xe||(xe.__webglTexture===void 0&&(xe.__webglTexture=s.createTexture()),xe.__version=b.version,f.memory.textures++),ge){Z.__webglFramebuffer=[];for(let De=0;De<6;De++)if(b.mipmaps&&b.mipmaps.length>0){Z.__webglFramebuffer[De]=[];for(let Je=0;Je<b.mipmaps.length;Je++)Z.__webglFramebuffer[De][Je]=s.createFramebuffer()}else Z.__webglFramebuffer[De]=s.createFramebuffer()}else{if(b.mipmaps&&b.mipmaps.length>0){Z.__webglFramebuffer=[];for(let De=0;De<b.mipmaps.length;De++)Z.__webglFramebuffer[De]=s.createFramebuffer()}else Z.__webglFramebuffer=s.createFramebuffer();if(Xe)for(let De=0,Je=Ee.length;De<Je;De++){const tt=r.get(Ee[De]);tt.__webglTexture===void 0&&(tt.__webglTexture=s.createTexture(),f.memory.textures++)}if(F.samples>0&&qt(F)===!1){Z.__webglMultisampledFramebuffer=s.createFramebuffer(),Z.__webglColorRenderbuffer=[],i.bindFramebuffer(s.FRAMEBUFFER,Z.__webglMultisampledFramebuffer);for(let De=0;De<Ee.length;De++){const Je=Ee[De];Z.__webglColorRenderbuffer[De]=s.createRenderbuffer(),s.bindRenderbuffer(s.RENDERBUFFER,Z.__webglColorRenderbuffer[De]);const tt=c.convert(Je.format,Je.colorSpace),Re=c.convert(Je.type),be=U(Je.internalFormat,tt,Re,Je.colorSpace,F.isXRRenderTarget===!0),Fe=k(F);s.renderbufferStorageMultisample(s.RENDERBUFFER,Fe,be,F.width,F.height),s.framebufferRenderbuffer(s.FRAMEBUFFER,s.COLOR_ATTACHMENT0+De,s.RENDERBUFFER,Z.__webglColorRenderbuffer[De])}s.bindRenderbuffer(s.RENDERBUFFER,null),F.depthBuffer&&(Z.__webglDepthRenderbuffer=s.createRenderbuffer(),Ge(Z.__webglDepthRenderbuffer,F,!0)),i.bindFramebuffer(s.FRAMEBUFFER,null)}}if(ge){i.bindTexture(s.TEXTURE_CUBE_MAP,xe.__webglTexture),j(s.TEXTURE_CUBE_MAP,b);for(let De=0;De<6;De++)if(b.mipmaps&&b.mipmaps.length>0)for(let Je=0;Je<b.mipmaps.length;Je++)Ae(Z.__webglFramebuffer[De][Je],F,b,s.COLOR_ATTACHMENT0,s.TEXTURE_CUBE_MAP_POSITIVE_X+De,Je);else Ae(Z.__webglFramebuffer[De],F,b,s.COLOR_ATTACHMENT0,s.TEXTURE_CUBE_MAP_POSITIVE_X+De,0);x(b)&&y(s.TEXTURE_CUBE_MAP),i.unbindTexture()}else if(Xe){for(let De=0,Je=Ee.length;De<Je;De++){const tt=Ee[De],Re=r.get(tt);let be=s.TEXTURE_2D;(F.isWebGL3DRenderTarget||F.isWebGLArrayRenderTarget)&&(be=F.isWebGL3DRenderTarget?s.TEXTURE_3D:s.TEXTURE_2D_ARRAY),i.bindTexture(be,Re.__webglTexture),j(be,tt),Ae(Z.__webglFramebuffer,F,tt,s.COLOR_ATTACHMENT0+De,be,0),x(tt)&&y(be)}i.unbindTexture()}else{let De=s.TEXTURE_2D;if((F.isWebGL3DRenderTarget||F.isWebGLArrayRenderTarget)&&(De=F.isWebGL3DRenderTarget?s.TEXTURE_3D:s.TEXTURE_2D_ARRAY),i.bindTexture(De,xe.__webglTexture),j(De,b),b.mipmaps&&b.mipmaps.length>0)for(let Je=0;Je<b.mipmaps.length;Je++)Ae(Z.__webglFramebuffer[Je],F,b,s.COLOR_ATTACHMENT0,De,Je);else Ae(Z.__webglFramebuffer,F,b,s.COLOR_ATTACHMENT0,De,0);x(b)&&y(De),i.unbindTexture()}F.depthBuffer&&qe(F)}function gt(F){const b=F.textures;for(let Z=0,xe=b.length;Z<xe;Z++){const Ee=b[Z];if(x(Ee)){const ge=T(F),Xe=r.get(Ee).__webglTexture;i.bindTexture(ge,Xe),y(ge),i.unbindTexture()}}}const Nt=[],lt=[];function Jt(F){if(F.samples>0){if(qt(F)===!1){const b=F.textures,Z=F.width,xe=F.height;let Ee=s.COLOR_BUFFER_BIT;const ge=F.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT,Xe=r.get(F),De=b.length>1;if(De)for(let tt=0;tt<b.length;tt++)i.bindFramebuffer(s.FRAMEBUFFER,Xe.__webglMultisampledFramebuffer),s.framebufferRenderbuffer(s.FRAMEBUFFER,s.COLOR_ATTACHMENT0+tt,s.RENDERBUFFER,null),i.bindFramebuffer(s.FRAMEBUFFER,Xe.__webglFramebuffer),s.framebufferTexture2D(s.DRAW_FRAMEBUFFER,s.COLOR_ATTACHMENT0+tt,s.TEXTURE_2D,null,0);i.bindFramebuffer(s.READ_FRAMEBUFFER,Xe.__webglMultisampledFramebuffer);const Je=F.texture.mipmaps;Je&&Je.length>0?i.bindFramebuffer(s.DRAW_FRAMEBUFFER,Xe.__webglFramebuffer[0]):i.bindFramebuffer(s.DRAW_FRAMEBUFFER,Xe.__webglFramebuffer);for(let tt=0;tt<b.length;tt++){if(F.resolveDepthBuffer&&(F.depthBuffer&&(Ee|=s.DEPTH_BUFFER_BIT),F.stencilBuffer&&F.resolveStencilBuffer&&(Ee|=s.STENCIL_BUFFER_BIT)),De){s.framebufferRenderbuffer(s.READ_FRAMEBUFFER,s.COLOR_ATTACHMENT0,s.RENDERBUFFER,Xe.__webglColorRenderbuffer[tt]);const Re=r.get(b[tt]).__webglTexture;s.framebufferTexture2D(s.DRAW_FRAMEBUFFER,s.COLOR_ATTACHMENT0,s.TEXTURE_2D,Re,0)}s.blitFramebuffer(0,0,Z,xe,0,0,Z,xe,Ee,s.NEAREST),m===!0&&(Nt.length=0,lt.length=0,Nt.push(s.COLOR_ATTACHMENT0+tt),F.depthBuffer&&F.resolveDepthBuffer===!1&&(Nt.push(ge),lt.push(ge),s.invalidateFramebuffer(s.DRAW_FRAMEBUFFER,lt)),s.invalidateFramebuffer(s.READ_FRAMEBUFFER,Nt))}if(i.bindFramebuffer(s.READ_FRAMEBUFFER,null),i.bindFramebuffer(s.DRAW_FRAMEBUFFER,null),De)for(let tt=0;tt<b.length;tt++){i.bindFramebuffer(s.FRAMEBUFFER,Xe.__webglMultisampledFramebuffer),s.framebufferRenderbuffer(s.FRAMEBUFFER,s.COLOR_ATTACHMENT0+tt,s.RENDERBUFFER,Xe.__webglColorRenderbuffer[tt]);const Re=r.get(b[tt]).__webglTexture;i.bindFramebuffer(s.FRAMEBUFFER,Xe.__webglFramebuffer),s.framebufferTexture2D(s.DRAW_FRAMEBUFFER,s.COLOR_ATTACHMENT0+tt,s.TEXTURE_2D,Re,0)}i.bindFramebuffer(s.DRAW_FRAMEBUFFER,Xe.__webglMultisampledFramebuffer)}else if(F.depthBuffer&&F.resolveDepthBuffer===!1&&m){const b=F.stencilBuffer?s.DEPTH_STENCIL_ATTACHMENT:s.DEPTH_ATTACHMENT;s.invalidateFramebuffer(s.DRAW_FRAMEBUFFER,[b])}}}function k(F){return Math.min(l.maxSamples,F.samples)}function qt(F){const b=r.get(F);return F.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&b.__useRenderToTexture!==!1}function bt(F){const b=f.render.frame;_.get(F)!==b&&(_.set(F,b),F.update())}function Ot(F,b){const Z=F.colorSpace,xe=F.format,Ee=F.type;return F.isCompressedTexture===!0||F.isVideoTexture===!0||Z!==Zr&&Z!==fs&&(Rt.getTransfer(Z)===Bt?(xe!==Li||Ee!==Si)&&st("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):At("WebGLTextures: Unsupported texture color space:",Z)),b}function Ye(F){return typeof HTMLImageElement<"u"&&F instanceof HTMLImageElement?(d.width=F.naturalWidth||F.width,d.height=F.naturalHeight||F.height):typeof VideoFrame<"u"&&F instanceof VideoFrame?(d.width=F.displayWidth,d.height=F.displayHeight):(d.width=F.width,d.height=F.height),d}this.allocateTextureUnit=re,this.resetTextureUnits=Y,this.setTexture2D=ee,this.setTexture2DArray=I,this.setTexture3D=B,this.setTextureCube=$,this.rebindTextures=$t,this.setupRenderTarget=yt,this.updateRenderTargetMipmap=gt,this.updateMultisampleRenderTarget=Jt,this.setupDepthRenderbuffer=qe,this.setupFrameBufferTexture=Ae,this.useMultisampledRTT=qt,this.isReversedDepthBuffer=function(){return i.buffers.depth.getReversed()}}function KC(s,e){function i(r,l=fs){let c;const f=Rt.getTransfer(l);if(r===Si)return s.UNSIGNED_BYTE;if(r===Ep)return s.UNSIGNED_SHORT_4_4_4_4;if(r===bp)return s.UNSIGNED_SHORT_5_5_5_1;if(r===cx)return s.UNSIGNED_INT_5_9_9_9_REV;if(r===ux)return s.UNSIGNED_INT_10F_11F_11F_REV;if(r===ox)return s.BYTE;if(r===lx)return s.SHORT;if(r===ol)return s.UNSIGNED_SHORT;if(r===Mp)return s.INT;if(r===Zi)return s.UNSIGNED_INT;if(r===Xi)return s.FLOAT;if(r===Ca)return s.HALF_FLOAT;if(r===fx)return s.ALPHA;if(r===hx)return s.RGB;if(r===Li)return s.RGBA;if(r===wa)return s.DEPTH_COMPONENT;if(r===ks)return s.DEPTH_STENCIL;if(r===dx)return s.RED;if(r===Tp)return s.RED_INTEGER;if(r===Yr)return s.RG;if(r===Ap)return s.RG_INTEGER;if(r===Rp)return s.RGBA_INTEGER;if(r===su||r===ru||r===ou||r===lu)if(f===Bt)if(c=e.get("WEBGL_compressed_texture_s3tc_srgb"),c!==null){if(r===su)return c.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(r===ru)return c.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(r===ou)return c.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(r===lu)return c.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(c=e.get("WEBGL_compressed_texture_s3tc"),c!==null){if(r===su)return c.COMPRESSED_RGB_S3TC_DXT1_EXT;if(r===ru)return c.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(r===ou)return c.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(r===lu)return c.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(r===Dd||r===Nd||r===Ud||r===Ld)if(c=e.get("WEBGL_compressed_texture_pvrtc"),c!==null){if(r===Dd)return c.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(r===Nd)return c.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(r===Ud)return c.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(r===Ld)return c.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(r===Od||r===Pd||r===Fd||r===Id||r===zd||r===Bd||r===Hd)if(c=e.get("WEBGL_compressed_texture_etc"),c!==null){if(r===Od||r===Pd)return f===Bt?c.COMPRESSED_SRGB8_ETC2:c.COMPRESSED_RGB8_ETC2;if(r===Fd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:c.COMPRESSED_RGBA8_ETC2_EAC;if(r===Id)return c.COMPRESSED_R11_EAC;if(r===zd)return c.COMPRESSED_SIGNED_R11_EAC;if(r===Bd)return c.COMPRESSED_RG11_EAC;if(r===Hd)return c.COMPRESSED_SIGNED_RG11_EAC}else return null;if(r===Gd||r===Vd||r===kd||r===jd||r===Xd||r===Wd||r===qd||r===Yd||r===Zd||r===Kd||r===Qd||r===Jd||r===$d||r===ep)if(c=e.get("WEBGL_compressed_texture_astc"),c!==null){if(r===Gd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:c.COMPRESSED_RGBA_ASTC_4x4_KHR;if(r===Vd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:c.COMPRESSED_RGBA_ASTC_5x4_KHR;if(r===kd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:c.COMPRESSED_RGBA_ASTC_5x5_KHR;if(r===jd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:c.COMPRESSED_RGBA_ASTC_6x5_KHR;if(r===Xd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:c.COMPRESSED_RGBA_ASTC_6x6_KHR;if(r===Wd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:c.COMPRESSED_RGBA_ASTC_8x5_KHR;if(r===qd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:c.COMPRESSED_RGBA_ASTC_8x6_KHR;if(r===Yd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:c.COMPRESSED_RGBA_ASTC_8x8_KHR;if(r===Zd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:c.COMPRESSED_RGBA_ASTC_10x5_KHR;if(r===Kd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:c.COMPRESSED_RGBA_ASTC_10x6_KHR;if(r===Qd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:c.COMPRESSED_RGBA_ASTC_10x8_KHR;if(r===Jd)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:c.COMPRESSED_RGBA_ASTC_10x10_KHR;if(r===$d)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:c.COMPRESSED_RGBA_ASTC_12x10_KHR;if(r===ep)return f===Bt?c.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:c.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(r===tp||r===np||r===ip)if(c=e.get("EXT_texture_compression_bptc"),c!==null){if(r===tp)return f===Bt?c.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:c.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(r===np)return c.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(r===ip)return c.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(r===ap||r===sp||r===rp||r===op)if(c=e.get("EXT_texture_compression_rgtc"),c!==null){if(r===ap)return c.COMPRESSED_RED_RGTC1_EXT;if(r===sp)return c.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(r===rp)return c.COMPRESSED_RED_GREEN_RGTC2_EXT;if(r===op)return c.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return r===ll?s.UNSIGNED_INT_24_8:s[r]!==void 0?s[r]:null}return{convert:i}}const QC=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,JC=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`;class $C{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,i){if(this.texture===null){const r=new Ex(e.texture);(e.depthNear!==i.depthNear||e.depthFar!==i.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=r}}getMesh(e){if(this.texture!==null&&this.mesh===null){const i=e.cameras[0].viewport,r=new Ki({vertexShader:QC,fragmentShader:JC,uniforms:{depthColor:{value:this.texture},depthWidth:{value:i.z},depthHeight:{value:i.w}}});this.mesh=new Na(new Su(20,20),r)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class e3 extends Xs{constructor(e,i){super();const r=this;let l=null,c=1,f=null,p="local-floor",m=1,d=null,_=null,v=null,g=null,M=null,E=null;const R=typeof XRWebGLBinding<"u",x=new $C,y={},T=i.getContextAttributes();let U=null,P=null;const V=[],H=[],z=new mt;let A=null;const L=new yi;L.viewport=new rn;const pe=new yi;pe.viewport=new rn;const w=[L,pe],Y=new uT;let re=null,fe=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(ie){let Se=V[ie];return Se===void 0&&(Se=new Wh,V[ie]=Se),Se.getTargetRaySpace()},this.getControllerGrip=function(ie){let Se=V[ie];return Se===void 0&&(Se=new Wh,V[ie]=Se),Se.getGripSpace()},this.getHand=function(ie){let Se=V[ie];return Se===void 0&&(Se=new Wh,V[ie]=Se),Se.getHandSpace()};function ee(ie){const Se=H.indexOf(ie.inputSource);if(Se===-1)return;const Ae=V[Se];Ae!==void 0&&(Ae.update(ie.inputSource,ie.frame,d||f),Ae.dispatchEvent({type:ie.type,data:ie.inputSource}))}function I(){l.removeEventListener("select",ee),l.removeEventListener("selectstart",ee),l.removeEventListener("selectend",ee),l.removeEventListener("squeeze",ee),l.removeEventListener("squeezestart",ee),l.removeEventListener("squeezeend",ee),l.removeEventListener("end",I),l.removeEventListener("inputsourceschange",B);for(let ie=0;ie<V.length;ie++){const Se=H[ie];Se!==null&&(H[ie]=null,V[ie].disconnect(Se))}re=null,fe=null,x.reset();for(const ie in y)delete y[ie];e.setRenderTarget(U),M=null,g=null,v=null,l=null,P=null,Ne.stop(),r.isPresenting=!1,e.setPixelRatio(A),e.setSize(z.width,z.height,!1),r.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(ie){c=ie,r.isPresenting===!0&&st("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(ie){p=ie,r.isPresenting===!0&&st("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return d||f},this.setReferenceSpace=function(ie){d=ie},this.getBaseLayer=function(){return g!==null?g:M},this.getBinding=function(){return v===null&&R&&(v=new XRWebGLBinding(l,i)),v},this.getFrame=function(){return E},this.getSession=function(){return l},this.setSession=async function(ie){if(l=ie,l!==null){if(U=e.getRenderTarget(),l.addEventListener("select",ee),l.addEventListener("selectstart",ee),l.addEventListener("selectend",ee),l.addEventListener("squeeze",ee),l.addEventListener("squeezestart",ee),l.addEventListener("squeezeend",ee),l.addEventListener("end",I),l.addEventListener("inputsourceschange",B),T.xrCompatible!==!0&&await i.makeXRCompatible(),A=e.getPixelRatio(),e.getSize(z),R&&"createProjectionLayer"in XRWebGLBinding.prototype){let Ae=null,Ge=null,Qe=null;T.depth&&(Qe=T.stencil?i.DEPTH24_STENCIL8:i.DEPTH_COMPONENT24,Ae=T.stencil?ks:wa,Ge=T.stencil?ll:Zi);const qe={colorFormat:i.RGBA8,depthFormat:Qe,scaleFactor:c};v=this.getBinding(),g=v.createProjectionLayer(qe),l.updateRenderState({layers:[g]}),e.setPixelRatio(1),e.setSize(g.textureWidth,g.textureHeight,!1),P=new Yi(g.textureWidth,g.textureHeight,{format:Li,type:Si,depthTexture:new cl(g.textureWidth,g.textureHeight,Ge,void 0,void 0,void 0,void 0,void 0,void 0,Ae),stencilBuffer:T.stencil,colorSpace:e.outputColorSpace,samples:T.antialias?4:0,resolveDepthBuffer:g.ignoreDepthValues===!1,resolveStencilBuffer:g.ignoreDepthValues===!1})}else{const Ae={antialias:T.antialias,alpha:!0,depth:T.depth,stencil:T.stencil,framebufferScaleFactor:c};M=new XRWebGLLayer(l,i,Ae),l.updateRenderState({baseLayer:M}),e.setPixelRatio(1),e.setSize(M.framebufferWidth,M.framebufferHeight,!1),P=new Yi(M.framebufferWidth,M.framebufferHeight,{format:Li,type:Si,colorSpace:e.outputColorSpace,stencilBuffer:T.stencil,resolveDepthBuffer:M.ignoreDepthValues===!1,resolveStencilBuffer:M.ignoreDepthValues===!1})}P.isXRRenderTarget=!0,this.setFoveation(m),d=null,f=await l.requestReferenceSpace(p),Ne.setContext(l),Ne.start(),r.isPresenting=!0,r.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(l!==null)return l.environmentBlendMode},this.getDepthTexture=function(){return x.getDepthTexture()};function B(ie){for(let Se=0;Se<ie.removed.length;Se++){const Ae=ie.removed[Se],Ge=H.indexOf(Ae);Ge>=0&&(H[Ge]=null,V[Ge].disconnect(Ae))}for(let Se=0;Se<ie.added.length;Se++){const Ae=ie.added[Se];let Ge=H.indexOf(Ae);if(Ge===-1){for(let qe=0;qe<V.length;qe++)if(qe>=H.length){H.push(Ae),Ge=qe;break}else if(H[qe]===null){H[qe]=Ae,Ge=qe;break}if(Ge===-1)break}const Qe=V[Ge];Qe&&Qe.connect(Ae)}}const $=new se,Q=new se;function de(ie,Se,Ae){$.setFromMatrixPosition(Se.matrixWorld),Q.setFromMatrixPosition(Ae.matrixWorld);const Ge=$.distanceTo(Q),Qe=Se.projectionMatrix.elements,qe=Ae.projectionMatrix.elements,$t=Qe[14]/(Qe[10]-1),yt=Qe[14]/(Qe[10]+1),gt=(Qe[9]+1)/Qe[5],Nt=(Qe[9]-1)/Qe[5],lt=(Qe[8]-1)/Qe[0],Jt=(qe[8]+1)/qe[0],k=$t*lt,qt=$t*Jt,bt=Ge/(-lt+Jt),Ot=bt*-lt;if(Se.matrixWorld.decompose(ie.position,ie.quaternion,ie.scale),ie.translateX(Ot),ie.translateZ(bt),ie.matrixWorld.compose(ie.position,ie.quaternion,ie.scale),ie.matrixWorldInverse.copy(ie.matrixWorld).invert(),Qe[10]===-1)ie.projectionMatrix.copy(Se.projectionMatrix),ie.projectionMatrixInverse.copy(Se.projectionMatrixInverse);else{const Ye=$t+bt,F=yt+bt,b=k-Ot,Z=qt+(Ge-Ot),xe=gt*yt/F*Ye,Ee=Nt*yt/F*Ye;ie.projectionMatrix.makePerspective(b,Z,xe,Ee,Ye,F),ie.projectionMatrixInverse.copy(ie.projectionMatrix).invert()}}function O(ie,Se){Se===null?ie.matrixWorld.copy(ie.matrix):ie.matrixWorld.multiplyMatrices(Se.matrixWorld,ie.matrix),ie.matrixWorldInverse.copy(ie.matrixWorld).invert()}this.updateCamera=function(ie){if(l===null)return;let Se=ie.near,Ae=ie.far;x.texture!==null&&(x.depthNear>0&&(Se=x.depthNear),x.depthFar>0&&(Ae=x.depthFar)),Y.near=pe.near=L.near=Se,Y.far=pe.far=L.far=Ae,(re!==Y.near||fe!==Y.far)&&(l.updateRenderState({depthNear:Y.near,depthFar:Y.far}),re=Y.near,fe=Y.far),Y.layers.mask=ie.layers.mask|6,L.layers.mask=Y.layers.mask&-5,pe.layers.mask=Y.layers.mask&-3;const Ge=ie.parent,Qe=Y.cameras;O(Y,Ge);for(let qe=0;qe<Qe.length;qe++)O(Qe[qe],Ge);Qe.length===2?de(Y,L,pe):Y.projectionMatrix.copy(L.projectionMatrix),j(ie,Y,Ge)};function j(ie,Se,Ae){Ae===null?ie.matrix.copy(Se.matrixWorld):(ie.matrix.copy(Ae.matrixWorld),ie.matrix.invert(),ie.matrix.multiply(Se.matrixWorld)),ie.matrix.decompose(ie.position,ie.quaternion,ie.scale),ie.updateMatrixWorld(!0),ie.projectionMatrix.copy(Se.projectionMatrix),ie.projectionMatrixInverse.copy(Se.projectionMatrixInverse),ie.isPerspectiveCamera&&(ie.fov=lp*2*Math.atan(1/ie.projectionMatrix.elements[5]),ie.zoom=1)}this.getCamera=function(){return Y},this.getFoveation=function(){if(!(g===null&&M===null))return m},this.setFoveation=function(ie){m=ie,g!==null&&(g.fixedFoveation=ie),M!==null&&M.fixedFoveation!==void 0&&(M.fixedFoveation=ie)},this.hasDepthSensing=function(){return x.texture!==null},this.getDepthSensingMesh=function(){return x.getMesh(Y)},this.getCameraTexture=function(ie){return y[ie]};let ve=null;function he(ie,Se){if(_=Se.getViewerPose(d||f),E=Se,_!==null){const Ae=_.views;M!==null&&(e.setRenderTargetFramebuffer(P,M.framebuffer),e.setRenderTarget(P));let Ge=!1;Ae.length!==Y.cameras.length&&(Y.cameras.length=0,Ge=!0);for(let yt=0;yt<Ae.length;yt++){const gt=Ae[yt];let Nt=null;if(M!==null)Nt=M.getViewport(gt);else{const Jt=v.getViewSubImage(g,gt);Nt=Jt.viewport,yt===0&&(e.setRenderTargetTextures(P,Jt.colorTexture,Jt.depthStencilTexture),e.setRenderTarget(P))}let lt=w[yt];lt===void 0&&(lt=new yi,lt.layers.enable(yt),lt.viewport=new rn,w[yt]=lt),lt.matrix.fromArray(gt.transform.matrix),lt.matrix.decompose(lt.position,lt.quaternion,lt.scale),lt.projectionMatrix.fromArray(gt.projectionMatrix),lt.projectionMatrixInverse.copy(lt.projectionMatrix).invert(),lt.viewport.set(Nt.x,Nt.y,Nt.width,Nt.height),yt===0&&(Y.matrix.copy(lt.matrix),Y.matrix.decompose(Y.position,Y.quaternion,Y.scale)),Ge===!0&&Y.cameras.push(lt)}const Qe=l.enabledFeatures;if(Qe&&Qe.includes("depth-sensing")&&l.depthUsage=="gpu-optimized"&&R){v=r.getBinding();const yt=v.getDepthInformation(Ae[0]);yt&&yt.isValid&&yt.texture&&x.init(yt,l.renderState)}if(Qe&&Qe.includes("camera-access")&&R){e.state.unbindTexture(),v=r.getBinding();for(let yt=0;yt<Ae.length;yt++){const gt=Ae[yt].camera;if(gt){let Nt=y[gt];Nt||(Nt=new Ex,y[gt]=Nt);const lt=v.getCameraImage(gt);Nt.sourceTexture=lt}}}}for(let Ae=0;Ae<V.length;Ae++){const Ge=H[Ae],Qe=V[Ae];Ge!==null&&Qe!==void 0&&Qe.update(Ge,Se,d||f)}ve&&ve(ie,Se),Se.detectedPlanes&&r.dispatchEvent({type:"planesdetected",data:Se}),E=null}const Ne=new Rx;Ne.setAnimationLoop(he),this.setAnimationLoop=function(ie){ve=ie},this.dispose=function(){}}}const Bs=new Da,t3=new nn;function n3(s,e){function i(x,y){x.matrixAutoUpdate===!0&&x.updateMatrix(),y.value.copy(x.matrix)}function r(x,y){y.color.getRGB(x.fogColor.value,bx(s)),y.isFog?(x.fogNear.value=y.near,x.fogFar.value=y.far):y.isFogExp2&&(x.fogDensity.value=y.density)}function l(x,y,T,U,P){y.isMeshBasicMaterial?c(x,y):y.isMeshLambertMaterial?(c(x,y),y.envMap&&(x.envMapIntensity.value=y.envMapIntensity)):y.isMeshToonMaterial?(c(x,y),v(x,y)):y.isMeshPhongMaterial?(c(x,y),_(x,y),y.envMap&&(x.envMapIntensity.value=y.envMapIntensity)):y.isMeshStandardMaterial?(c(x,y),g(x,y),y.isMeshPhysicalMaterial&&M(x,y,P)):y.isMeshMatcapMaterial?(c(x,y),E(x,y)):y.isMeshDepthMaterial?c(x,y):y.isMeshDistanceMaterial?(c(x,y),R(x,y)):y.isMeshNormalMaterial?c(x,y):y.isLineBasicMaterial?(f(x,y),y.isLineDashedMaterial&&p(x,y)):y.isPointsMaterial?m(x,y,T,U):y.isSpriteMaterial?d(x,y):y.isShadowMaterial?(x.color.value.copy(y.color),x.opacity.value=y.opacity):y.isShaderMaterial&&(y.uniformsNeedUpdate=!1)}function c(x,y){x.opacity.value=y.opacity,y.color&&x.diffuse.value.copy(y.color),y.emissive&&x.emissive.value.copy(y.emissive).multiplyScalar(y.emissiveIntensity),y.map&&(x.map.value=y.map,i(y.map,x.mapTransform)),y.alphaMap&&(x.alphaMap.value=y.alphaMap,i(y.alphaMap,x.alphaMapTransform)),y.bumpMap&&(x.bumpMap.value=y.bumpMap,i(y.bumpMap,x.bumpMapTransform),x.bumpScale.value=y.bumpScale,y.side===Zn&&(x.bumpScale.value*=-1)),y.normalMap&&(x.normalMap.value=y.normalMap,i(y.normalMap,x.normalMapTransform),x.normalScale.value.copy(y.normalScale),y.side===Zn&&x.normalScale.value.negate()),y.displacementMap&&(x.displacementMap.value=y.displacementMap,i(y.displacementMap,x.displacementMapTransform),x.displacementScale.value=y.displacementScale,x.displacementBias.value=y.displacementBias),y.emissiveMap&&(x.emissiveMap.value=y.emissiveMap,i(y.emissiveMap,x.emissiveMapTransform)),y.specularMap&&(x.specularMap.value=y.specularMap,i(y.specularMap,x.specularMapTransform)),y.alphaTest>0&&(x.alphaTest.value=y.alphaTest);const T=e.get(y),U=T.envMap,P=T.envMapRotation;U&&(x.envMap.value=U,Bs.copy(P),Bs.x*=-1,Bs.y*=-1,Bs.z*=-1,U.isCubeTexture&&U.isRenderTargetTexture===!1&&(Bs.y*=-1,Bs.z*=-1),x.envMapRotation.value.setFromMatrix4(t3.makeRotationFromEuler(Bs)),x.flipEnvMap.value=U.isCubeTexture&&U.isRenderTargetTexture===!1?-1:1,x.reflectivity.value=y.reflectivity,x.ior.value=y.ior,x.refractionRatio.value=y.refractionRatio),y.lightMap&&(x.lightMap.value=y.lightMap,x.lightMapIntensity.value=y.lightMapIntensity,i(y.lightMap,x.lightMapTransform)),y.aoMap&&(x.aoMap.value=y.aoMap,x.aoMapIntensity.value=y.aoMapIntensity,i(y.aoMap,x.aoMapTransform))}function f(x,y){x.diffuse.value.copy(y.color),x.opacity.value=y.opacity,y.map&&(x.map.value=y.map,i(y.map,x.mapTransform))}function p(x,y){x.dashSize.value=y.dashSize,x.totalSize.value=y.dashSize+y.gapSize,x.scale.value=y.scale}function m(x,y,T,U){x.diffuse.value.copy(y.color),x.opacity.value=y.opacity,x.size.value=y.size*T,x.scale.value=U*.5,y.map&&(x.map.value=y.map,i(y.map,x.uvTransform)),y.alphaMap&&(x.alphaMap.value=y.alphaMap,i(y.alphaMap,x.alphaMapTransform)),y.alphaTest>0&&(x.alphaTest.value=y.alphaTest)}function d(x,y){x.diffuse.value.copy(y.color),x.opacity.value=y.opacity,x.rotation.value=y.rotation,y.map&&(x.map.value=y.map,i(y.map,x.mapTransform)),y.alphaMap&&(x.alphaMap.value=y.alphaMap,i(y.alphaMap,x.alphaMapTransform)),y.alphaTest>0&&(x.alphaTest.value=y.alphaTest)}function _(x,y){x.specular.value.copy(y.specular),x.shininess.value=Math.max(y.shininess,1e-4)}function v(x,y){y.gradientMap&&(x.gradientMap.value=y.gradientMap)}function g(x,y){x.metalness.value=y.metalness,y.metalnessMap&&(x.metalnessMap.value=y.metalnessMap,i(y.metalnessMap,x.metalnessMapTransform)),x.roughness.value=y.roughness,y.roughnessMap&&(x.roughnessMap.value=y.roughnessMap,i(y.roughnessMap,x.roughnessMapTransform)),y.envMap&&(x.envMapIntensity.value=y.envMapIntensity)}function M(x,y,T){x.ior.value=y.ior,y.sheen>0&&(x.sheenColor.value.copy(y.sheenColor).multiplyScalar(y.sheen),x.sheenRoughness.value=y.sheenRoughness,y.sheenColorMap&&(x.sheenColorMap.value=y.sheenColorMap,i(y.sheenColorMap,x.sheenColorMapTransform)),y.sheenRoughnessMap&&(x.sheenRoughnessMap.value=y.sheenRoughnessMap,i(y.sheenRoughnessMap,x.sheenRoughnessMapTransform))),y.clearcoat>0&&(x.clearcoat.value=y.clearcoat,x.clearcoatRoughness.value=y.clearcoatRoughness,y.clearcoatMap&&(x.clearcoatMap.value=y.clearcoatMap,i(y.clearcoatMap,x.clearcoatMapTransform)),y.clearcoatRoughnessMap&&(x.clearcoatRoughnessMap.value=y.clearcoatRoughnessMap,i(y.clearcoatRoughnessMap,x.clearcoatRoughnessMapTransform)),y.clearcoatNormalMap&&(x.clearcoatNormalMap.value=y.clearcoatNormalMap,i(y.clearcoatNormalMap,x.clearcoatNormalMapTransform),x.clearcoatNormalScale.value.copy(y.clearcoatNormalScale),y.side===Zn&&x.clearcoatNormalScale.value.negate())),y.dispersion>0&&(x.dispersion.value=y.dispersion),y.iridescence>0&&(x.iridescence.value=y.iridescence,x.iridescenceIOR.value=y.iridescenceIOR,x.iridescenceThicknessMinimum.value=y.iridescenceThicknessRange[0],x.iridescenceThicknessMaximum.value=y.iridescenceThicknessRange[1],y.iridescenceMap&&(x.iridescenceMap.value=y.iridescenceMap,i(y.iridescenceMap,x.iridescenceMapTransform)),y.iridescenceThicknessMap&&(x.iridescenceThicknessMap.value=y.iridescenceThicknessMap,i(y.iridescenceThicknessMap,x.iridescenceThicknessMapTransform))),y.transmission>0&&(x.transmission.value=y.transmission,x.transmissionSamplerMap.value=T.texture,x.transmissionSamplerSize.value.set(T.width,T.height),y.transmissionMap&&(x.transmissionMap.value=y.transmissionMap,i(y.transmissionMap,x.transmissionMapTransform)),x.thickness.value=y.thickness,y.thicknessMap&&(x.thicknessMap.value=y.thicknessMap,i(y.thicknessMap,x.thicknessMapTransform)),x.attenuationDistance.value=y.attenuationDistance,x.attenuationColor.value.copy(y.attenuationColor)),y.anisotropy>0&&(x.anisotropyVector.value.set(y.anisotropy*Math.cos(y.anisotropyRotation),y.anisotropy*Math.sin(y.anisotropyRotation)),y.anisotropyMap&&(x.anisotropyMap.value=y.anisotropyMap,i(y.anisotropyMap,x.anisotropyMapTransform))),x.specularIntensity.value=y.specularIntensity,x.specularColor.value.copy(y.specularColor),y.specularColorMap&&(x.specularColorMap.value=y.specularColorMap,i(y.specularColorMap,x.specularColorMapTransform)),y.specularIntensityMap&&(x.specularIntensityMap.value=y.specularIntensityMap,i(y.specularIntensityMap,x.specularIntensityMapTransform))}function E(x,y){y.matcap&&(x.matcap.value=y.matcap)}function R(x,y){const T=e.get(y).light;x.referencePosition.value.setFromMatrixPosition(T.matrixWorld),x.nearDistance.value=T.shadow.camera.near,x.farDistance.value=T.shadow.camera.far}return{refreshFogUniforms:r,refreshMaterialUniforms:l}}function i3(s,e,i,r){let l={},c={},f=[];const p=s.getParameter(s.MAX_UNIFORM_BUFFER_BINDINGS);function m(T,U){const P=U.program;r.uniformBlockBinding(T,P)}function d(T,U){let P=l[T.id];P===void 0&&(E(T),P=_(T),l[T.id]=P,T.addEventListener("dispose",x));const V=U.program;r.updateUBOMapping(T,V);const H=e.render.frame;c[T.id]!==H&&(g(T),c[T.id]=H)}function _(T){const U=v();T.__bindingPointIndex=U;const P=s.createBuffer(),V=T.__size,H=T.usage;return s.bindBuffer(s.UNIFORM_BUFFER,P),s.bufferData(s.UNIFORM_BUFFER,V,H),s.bindBuffer(s.UNIFORM_BUFFER,null),s.bindBufferBase(s.UNIFORM_BUFFER,U,P),P}function v(){for(let T=0;T<p;T++)if(f.indexOf(T)===-1)return f.push(T),T;return At("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function g(T){const U=l[T.id],P=T.uniforms,V=T.__cache;s.bindBuffer(s.UNIFORM_BUFFER,U);for(let H=0,z=P.length;H<z;H++){const A=Array.isArray(P[H])?P[H]:[P[H]];for(let L=0,pe=A.length;L<pe;L++){const w=A[L];if(M(w,H,L,V)===!0){const Y=w.__offset,re=Array.isArray(w.value)?w.value:[w.value];let fe=0;for(let ee=0;ee<re.length;ee++){const I=re[ee],B=R(I);typeof I=="number"||typeof I=="boolean"?(w.__data[0]=I,s.bufferSubData(s.UNIFORM_BUFFER,Y+fe,w.__data)):I.isMatrix3?(w.__data[0]=I.elements[0],w.__data[1]=I.elements[1],w.__data[2]=I.elements[2],w.__data[3]=0,w.__data[4]=I.elements[3],w.__data[5]=I.elements[4],w.__data[6]=I.elements[5],w.__data[7]=0,w.__data[8]=I.elements[6],w.__data[9]=I.elements[7],w.__data[10]=I.elements[8],w.__data[11]=0):(I.toArray(w.__data,fe),fe+=B.storage/Float32Array.BYTES_PER_ELEMENT)}s.bufferSubData(s.UNIFORM_BUFFER,Y,w.__data)}}}s.bindBuffer(s.UNIFORM_BUFFER,null)}function M(T,U,P,V){const H=T.value,z=U+"_"+P;if(V[z]===void 0)return typeof H=="number"||typeof H=="boolean"?V[z]=H:V[z]=H.clone(),!0;{const A=V[z];if(typeof H=="number"||typeof H=="boolean"){if(A!==H)return V[z]=H,!0}else if(A.equals(H)===!1)return A.copy(H),!0}return!1}function E(T){const U=T.uniforms;let P=0;const V=16;for(let z=0,A=U.length;z<A;z++){const L=Array.isArray(U[z])?U[z]:[U[z]];for(let pe=0,w=L.length;pe<w;pe++){const Y=L[pe],re=Array.isArray(Y.value)?Y.value:[Y.value];for(let fe=0,ee=re.length;fe<ee;fe++){const I=re[fe],B=R(I),$=P%V,Q=$%B.boundary,de=$+Q;P+=Q,de!==0&&V-de<B.storage&&(P+=V-de),Y.__data=new Float32Array(B.storage/Float32Array.BYTES_PER_ELEMENT),Y.__offset=P,P+=B.storage}}}const H=P%V;return H>0&&(P+=V-H),T.__size=P,T.__cache={},this}function R(T){const U={boundary:0,storage:0};return typeof T=="number"||typeof T=="boolean"?(U.boundary=4,U.storage=4):T.isVector2?(U.boundary=8,U.storage=8):T.isVector3||T.isColor?(U.boundary=16,U.storage=12):T.isVector4?(U.boundary=16,U.storage=16):T.isMatrix3?(U.boundary=48,U.storage=48):T.isMatrix4?(U.boundary=64,U.storage=64):T.isTexture?st("WebGLRenderer: Texture samplers can not be part of an uniforms group."):st("WebGLRenderer: Unsupported uniform value type.",T),U}function x(T){const U=T.target;U.removeEventListener("dispose",x);const P=f.indexOf(U.__bindingPointIndex);f.splice(P,1),s.deleteBuffer(l[U.id]),delete l[U.id],delete c[U.id]}function y(){for(const T in l)s.deleteBuffer(l[T]);f=[],l={},c={}}return{bind:m,update:d,dispose:y}}const a3=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]);let ki=null;function s3(){return ki===null&&(ki=new Kb(a3,16,16,Yr,Ca),ki.name="DFG_LUT",ki.minFilter=Nn,ki.magFilter=Nn,ki.wrapS=Ma,ki.wrapT=Ma,ki.generateMipmaps=!1,ki.needsUpdate=!0),ki}class r3{constructor(e={}){const{canvas:i=Ab(),context:r=null,depth:l=!0,stencil:c=!1,alpha:f=!1,antialias:p=!1,premultipliedAlpha:m=!0,preserveDrawingBuffer:d=!1,powerPreference:_="default",failIfMajorPerformanceCaveat:v=!1,reversedDepthBuffer:g=!1,outputBufferType:M=Si}=e;this.isWebGLRenderer=!0;let E;if(r!==null){if(typeof WebGLRenderingContext<"u"&&r instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");E=r.getContextAttributes().alpha}else E=f;const R=M,x=new Set([Rp,Ap,Tp]),y=new Set([Si,Zi,ol,ll,Ep,bp]),T=new Uint32Array(4),U=new Int32Array(4);let P=null,V=null;const H=[],z=[];let A=null;this.domElement=i,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=qi,this.toneMappingExposure=1,this.transmissionResolutionScale=1;const L=this;let pe=!1;this._outputColorSpace=xi;let w=0,Y=0,re=null,fe=-1,ee=null;const I=new rn,B=new rn;let $=null;const Q=new Lt(0);let de=0,O=i.width,j=i.height,ve=1,he=null,Ne=null;const ie=new rn(0,0,O,j),Se=new rn(0,0,O,j);let Ae=!1;const Ge=new yx;let Qe=!1,qe=!1;const $t=new nn,yt=new se,gt=new rn,Nt={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0};let lt=!1;function Jt(){return re===null?ve:1}let k=r;function qt(N,W){return i.getContext(N,W)}try{const N={alpha:!0,depth:l,stencil:c,antialias:p,premultipliedAlpha:m,preserveDrawingBuffer:d,powerPreference:_,failIfMajorPerformanceCaveat:v};if("setAttribute"in i&&i.setAttribute("data-engine",`three.js r${Sp}`),i.addEventListener("webglcontextlost",He,!1),i.addEventListener("webglcontextrestored",it,!1),i.addEventListener("webglcontextcreationerror",Ft,!1),k===null){const W="webgl2";if(k=qt(W,N),k===null)throw qt(W)?new Error("Error creating WebGL context with your selected attributes."):new Error("Error creating WebGL context.")}}catch(N){throw At("WebGLRenderer: "+N.message),N}let bt,Ot,Ye,F,b,Z,xe,Ee,ge,Xe,De,Je,tt,Re,be,Fe,Pe,Ie,ut,q,we,Ce,ze;function Te(){bt=new rR(k),bt.init(),we=new KC(k,bt),Ot=new J1(k,bt,e,we),Ye=new YC(k,bt),Ot.reversedDepthBuffer&&g&&Ye.buffers.depth.setReversed(!0),F=new cR(k),b=new OC,Z=new ZC(k,bt,Ye,b,Ot,we,F),xe=new sR(L),Ee=new pT(k),Ce=new K1(k,Ee),ge=new oR(k,Ee,F,Ce),Xe=new fR(k,ge,Ee,Ce,F),Ie=new uR(k,Ot,Z),be=new $1(b),De=new LC(L,xe,bt,Ot,Ce,be),Je=new n3(L,b),tt=new FC,Re=new VC(bt),Pe=new Z1(L,xe,Ye,Xe,E,m),Fe=new qC(L,Xe,Ot),ze=new i3(k,F,Ot,Ye),ut=new Q1(k,bt,F),q=new lR(k,bt,F),F.programs=De.programs,L.capabilities=Ot,L.extensions=bt,L.properties=b,L.renderLists=tt,L.shadowMap=Fe,L.state=Ye,L.info=F}Te(),R!==Si&&(A=new dR(R,i.width,i.height,l,c));const me=new e3(L,k);this.xr=me,this.getContext=function(){return k},this.getContextAttributes=function(){return k.getContextAttributes()},this.forceContextLoss=function(){const N=bt.get("WEBGL_lose_context");N&&N.loseContext()},this.forceContextRestore=function(){const N=bt.get("WEBGL_lose_context");N&&N.restoreContext()},this.getPixelRatio=function(){return ve},this.setPixelRatio=function(N){N!==void 0&&(ve=N,this.setSize(O,j,!1))},this.getSize=function(N){return N.set(O,j)},this.setSize=function(N,W,ce=!0){if(me.isPresenting){st("WebGLRenderer: Can't change size while VR device is presenting.");return}O=N,j=W,i.width=Math.floor(N*ve),i.height=Math.floor(W*ve),ce===!0&&(i.style.width=N+"px",i.style.height=W+"px"),A!==null&&A.setSize(i.width,i.height),this.setViewport(0,0,N,W)},this.getDrawingBufferSize=function(N){return N.set(O*ve,j*ve).floor()},this.setDrawingBufferSize=function(N,W,ce){O=N,j=W,ve=ce,i.width=Math.floor(N*ce),i.height=Math.floor(W*ce),this.setViewport(0,0,N,W)},this.setEffects=function(N){if(R===Si){console.error("THREE.WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(N){for(let W=0;W<N.length;W++)if(N[W].isOutputPass===!0){console.warn("THREE.WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}A.setEffects(N||[])},this.getCurrentViewport=function(N){return N.copy(I)},this.getViewport=function(N){return N.copy(ie)},this.setViewport=function(N,W,ce,oe){N.isVector4?ie.set(N.x,N.y,N.z,N.w):ie.set(N,W,ce,oe),Ye.viewport(I.copy(ie).multiplyScalar(ve).round())},this.getScissor=function(N){return N.copy(Se)},this.setScissor=function(N,W,ce,oe){N.isVector4?Se.set(N.x,N.y,N.z,N.w):Se.set(N,W,ce,oe),Ye.scissor(B.copy(Se).multiplyScalar(ve).round())},this.getScissorTest=function(){return Ae},this.setScissorTest=function(N){Ye.setScissorTest(Ae=N)},this.setOpaqueSort=function(N){he=N},this.setTransparentSort=function(N){Ne=N},this.getClearColor=function(N){return N.copy(Pe.getClearColor())},this.setClearColor=function(){Pe.setClearColor(...arguments)},this.getClearAlpha=function(){return Pe.getClearAlpha()},this.setClearAlpha=function(){Pe.setClearAlpha(...arguments)},this.clear=function(N=!0,W=!0,ce=!0){let oe=0;if(N){let te=!1;if(re!==null){const Ue=re.texture.format;te=x.has(Ue)}if(te){const Ue=re.texture.type,Be=y.has(Ue),Le=Pe.getClearColor(),We=Pe.getClearAlpha(),Ke=Le.r,nt=Le.g,rt=Le.b;Be?(T[0]=Ke,T[1]=nt,T[2]=rt,T[3]=We,k.clearBufferuiv(k.COLOR,0,T)):(U[0]=Ke,U[1]=nt,U[2]=rt,U[3]=We,k.clearBufferiv(k.COLOR,0,U))}else oe|=k.COLOR_BUFFER_BIT}W&&(oe|=k.DEPTH_BUFFER_BIT),ce&&(oe|=k.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),oe!==0&&k.clear(oe)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.dispose=function(){i.removeEventListener("webglcontextlost",He,!1),i.removeEventListener("webglcontextrestored",it,!1),i.removeEventListener("webglcontextcreationerror",Ft,!1),Pe.dispose(),tt.dispose(),Re.dispose(),b.dispose(),xe.dispose(),Xe.dispose(),Ce.dispose(),ze.dispose(),De.dispose(),me.dispose(),me.removeEventListener("sessionstart",qs),me.removeEventListener("sessionend",Ys),Ii.stop()};function He(N){N.preventDefault(),I0("WebGLRenderer: Context Lost."),pe=!0}function it(){I0("WebGLRenderer: Context Restored."),pe=!1;const N=F.autoReset,W=Fe.enabled,ce=Fe.autoUpdate,oe=Fe.needsUpdate,te=Fe.type;Te(),F.autoReset=N,Fe.enabled=W,Fe.autoUpdate=ce,Fe.needsUpdate=oe,Fe.type=te}function Ft(N){At("WebGLRenderer: A WebGL context could not be created. Reason: ",N.statusMessage)}function Tt(N){const W=N.target;W.removeEventListener("dispose",Tt),Ln(W)}function Ln(N){Mi(N),b.remove(N)}function Mi(N){const W=b.get(N).programs;W!==void 0&&(W.forEach(function(ce){De.releaseProgram(ce)}),N.isShaderMaterial&&De.releaseShaderCache(N))}this.renderBufferDirect=function(N,W,ce,oe,te,Ue){W===null&&(W=Nt);const Be=te.isMesh&&te.matrixWorld.determinant()<0,Le=xl(N,W,ce,oe,te);Ye.setMaterial(oe,Be);let We=ce.index,Ke=1;if(oe.wireframe===!0){if(We=ge.getWireframeAttribute(ce),We===void 0)return;Ke=2}const nt=ce.drawRange,rt=ce.attributes.position;let Ve=nt.start*Ke,ft=(nt.start+nt.count)*Ke;Ue!==null&&(Ve=Math.max(Ve,Ue.start*Ke),ft=Math.min(ft,(Ue.start+Ue.count)*Ke)),We!==null?(Ve=Math.max(Ve,0),ft=Math.min(ft,We.count)):rt!=null&&(Ve=Math.max(Ve,0),ft=Math.min(ft,rt.count));const Yt=ft-Ve;if(Yt<0||Yt===1/0)return;Ce.setup(te,oe,Le,ce,We);let Zt,Ct=ut;if(We!==null&&(Zt=Ee.get(We),Ct=q,Ct.setIndex(Zt)),te.isMesh)oe.wireframe===!0?(Ye.setLineWidth(oe.wireframeLinewidth*Jt()),Ct.setMode(k.LINES)):Ct.setMode(k.TRIANGLES);else if(te.isLine){let gn=oe.linewidth;gn===void 0&&(gn=1),Ye.setLineWidth(gn*Jt()),te.isLineSegments?Ct.setMode(k.LINES):te.isLineLoop?Ct.setMode(k.LINE_LOOP):Ct.setMode(k.LINE_STRIP)}else te.isPoints?Ct.setMode(k.POINTS):te.isSprite&&Ct.setMode(k.TRIANGLES);if(te.isBatchedMesh)if(te._multiDrawInstances!==null)mu("WebGLRenderer: renderMultiDrawInstances has been deprecated and will be removed in r184. Append to renderMultiDraw arguments and use indirection."),Ct.renderMultiDrawInstances(te._multiDrawStarts,te._multiDrawCounts,te._multiDrawCount,te._multiDrawInstances);else if(bt.get("WEBGL_multi_draw"))Ct.renderMultiDraw(te._multiDrawStarts,te._multiDrawCounts,te._multiDrawCount);else{const gn=te._multiDrawStarts,je=te._multiDrawCounts,On=te._multiDrawCount,at=We?Ee.get(We).bytesPerElement:1,Pn=b.get(oe).currentProgram.getUniforms();for(let Qn=0;Qn<On;Qn++)Pn.setValue(k,"_gl_DrawID",Qn),Ct.render(gn[Qn]/at,je[Qn])}else if(te.isInstancedMesh)Ct.renderInstances(Ve,Yt,te.count);else if(ce.isInstancedBufferGeometry){const gn=ce._maxInstanceCount!==void 0?ce._maxInstanceCount:1/0,je=Math.min(ce.instanceCount,gn);Ct.renderInstances(Ve,Yt,je)}else Ct.render(Ve,Yt)};function to(N,W,ce){N.transparent===!0&&N.side===Sa&&N.forceSinglePass===!1?(N.side=Zn,N.needsUpdate=!0,Ua(N,W,ce),N.side=ds,N.needsUpdate=!0,Ua(N,W,ce),N.side=Sa):Ua(N,W,ce)}this.compile=function(N,W,ce=null){ce===null&&(ce=N),V=Re.get(ce),V.init(W),z.push(V),ce.traverseVisible(function(te){te.isLight&&te.layers.test(W.layers)&&(V.pushLight(te),te.castShadow&&V.pushShadow(te))}),N!==ce&&N.traverseVisible(function(te){te.isLight&&te.layers.test(W.layers)&&(V.pushLight(te),te.castShadow&&V.pushShadow(te))}),V.setupLights();const oe=new Set;return N.traverse(function(te){if(!(te.isMesh||te.isPoints||te.isLine||te.isSprite))return;const Ue=te.material;if(Ue)if(Array.isArray(Ue))for(let Be=0;Be<Ue.length;Be++){const Le=Ue[Be];to(Le,ce,te),oe.add(Le)}else to(Ue,ce,te),oe.add(Ue)}),V=z.pop(),oe},this.compileAsync=function(N,W,ce=null){const oe=this.compile(N,W,ce);return new Promise(te=>{function Ue(){if(oe.forEach(function(Be){b.get(Be).currentProgram.isReady()&&oe.delete(Be)}),oe.size===0){te(N);return}setTimeout(Ue,10)}bt.get("KHR_parallel_shader_compile")!==null?Ue():setTimeout(Ue,10)})};let Ws=null;function gl(N){Ws&&Ws(N)}function qs(){Ii.stop()}function Ys(){Ii.start()}const Ii=new Rx;Ii.setAnimationLoop(gl),typeof self<"u"&&Ii.setContext(self),this.setAnimationLoop=function(N){Ws=N,me.setAnimationLoop(N),N===null?Ii.stop():Ii.start()},me.addEventListener("sessionstart",qs),me.addEventListener("sessionend",Ys),this.render=function(N,W){if(W!==void 0&&W.isCamera!==!0){At("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(pe===!0)return;const ce=me.enabled===!0&&me.isPresenting===!0,oe=A!==null&&(re===null||ce)&&A.begin(L,re);if(N.matrixWorldAutoUpdate===!0&&N.updateMatrixWorld(),W.parent===null&&W.matrixWorldAutoUpdate===!0&&W.updateMatrixWorld(),me.enabled===!0&&me.isPresenting===!0&&(A===null||A.isCompositing()===!1)&&(me.cameraAutoUpdate===!0&&me.updateCamera(W),W=me.getCamera()),N.isScene===!0&&N.onBeforeRender(L,N,W,re),V=Re.get(N,z.length),V.init(W),z.push(V),$t.multiplyMatrices(W.projectionMatrix,W.matrixWorldInverse),Ge.setFromProjectionMatrix($t,Wi,W.reversedDepth),qe=this.localClippingEnabled,Qe=be.init(this.clippingPlanes,qe),P=tt.get(N,H.length),P.init(),H.push(P),me.enabled===!0&&me.isPresenting===!0){const Be=L.xr.getDepthSensingMesh();Be!==null&&Zs(Be,W,-1/0,L.sortObjects)}Zs(N,W,0,L.sortObjects),P.finish(),L.sortObjects===!0&&P.sort(he,Ne),lt=me.enabled===!1||me.isPresenting===!1||me.hasDepthSensing()===!1,lt&&Pe.addToRenderList(P,N),this.info.render.frame++,Qe===!0&&be.beginShadows();const te=V.state.shadowsArray;if(Fe.render(te,N,W),Qe===!0&&be.endShadows(),this.info.autoReset===!0&&this.info.reset(),(oe&&A.hasRenderPass())===!1){const Be=P.opaque,Le=P.transmissive;if(V.setupLights(),W.isArrayCamera){const We=W.cameras;if(Le.length>0)for(let Ke=0,nt=We.length;Ke<nt;Ke++){const rt=We[Ke];on(Be,Le,N,rt)}lt&&Pe.render(N);for(let Ke=0,nt=We.length;Ke<nt;Ke++){const rt=We[Ke];Ei(P,N,rt,rt.viewport)}}else Le.length>0&&on(Be,Le,N,W),lt&&Pe.render(N),Ei(P,N,W)}re!==null&&Y===0&&(Z.updateMultisampleRenderTarget(re),Z.updateRenderTargetMipmap(re)),oe&&A.end(L),N.isScene===!0&&N.onAfterRender(L,N,W),Ce.resetDefaultState(),fe=-1,ee=null,z.pop(),z.length>0?(V=z[z.length-1],Qe===!0&&be.setGlobalState(L.clippingPlanes,V.state.camera)):V=null,H.pop(),H.length>0?P=H[H.length-1]:P=null};function Zs(N,W,ce,oe){if(N.visible===!1)return;if(N.layers.test(W.layers)){if(N.isGroup)ce=N.renderOrder;else if(N.isLOD)N.autoUpdate===!0&&N.update(W);else if(N.isLight)V.pushLight(N),N.castShadow&&V.pushShadow(N);else if(N.isSprite){if(!N.frustumCulled||Ge.intersectsSprite(N)){oe&&gt.setFromMatrixPosition(N.matrixWorld).applyMatrix4($t);const Be=Xe.update(N),Le=N.material;Le.visible&&P.push(N,Be,Le,ce,gt.z,null)}}else if((N.isMesh||N.isLine||N.isPoints)&&(!N.frustumCulled||Ge.intersectsObject(N))){const Be=Xe.update(N),Le=N.material;if(oe&&(N.boundingSphere!==void 0?(N.boundingSphere===null&&N.computeBoundingSphere(),gt.copy(N.boundingSphere.center)):(Be.boundingSphere===null&&Be.computeBoundingSphere(),gt.copy(Be.boundingSphere.center)),gt.applyMatrix4(N.matrixWorld).applyMatrix4($t)),Array.isArray(Le)){const We=Be.groups;for(let Ke=0,nt=We.length;Ke<nt;Ke++){const rt=We[Ke],Ve=Le[rt.materialIndex];Ve&&Ve.visible&&P.push(N,Be,Ve,ce,gt.z,rt)}}else Le.visible&&P.push(N,Be,Le,ce,gt.z,null)}}const Ue=N.children;for(let Be=0,Le=Ue.length;Be<Le;Be++)Zs(Ue[Be],W,ce,oe)}function Ei(N,W,ce,oe){const{opaque:te,transmissive:Ue,transparent:Be}=N;V.setupLightsView(ce),Qe===!0&&be.setGlobalState(L.clippingPlanes,ce),oe&&Ye.viewport(I.copy(oe)),te.length>0&&mn(te,W,ce),Ue.length>0&&mn(Ue,W,ce),Be.length>0&&mn(Be,W,ce),Ye.buffers.depth.setTest(!0),Ye.buffers.depth.setMask(!0),Ye.buffers.color.setMask(!0),Ye.setPolygonOffset(!1)}function on(N,W,ce,oe){if((ce.isScene===!0?ce.overrideMaterial:null)!==null)return;if(V.state.transmissionRenderTarget[oe.id]===void 0){const Ve=bt.has("EXT_color_buffer_half_float")||bt.has("EXT_color_buffer_float");V.state.transmissionRenderTarget[oe.id]=new Yi(1,1,{generateMipmaps:!0,type:Ve?Ca:Si,minFilter:Vs,samples:Ot.samples,stencilBuffer:c,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:Rt.workingColorSpace})}const Ue=V.state.transmissionRenderTarget[oe.id],Be=oe.viewport||I;Ue.setSize(Be.z*L.transmissionResolutionScale,Be.w*L.transmissionResolutionScale);const Le=L.getRenderTarget(),We=L.getActiveCubeFace(),Ke=L.getActiveMipmapLevel();L.setRenderTarget(Ue),L.getClearColor(Q),de=L.getClearAlpha(),de<1&&L.setClearColor(16777215,.5),L.clear(),lt&&Pe.render(ce);const nt=L.toneMapping;L.toneMapping=qi;const rt=oe.viewport;if(oe.viewport!==void 0&&(oe.viewport=void 0),V.setupLightsView(oe),Qe===!0&&be.setGlobalState(L.clippingPlanes,oe),mn(N,ce,oe),Z.updateMultisampleRenderTarget(Ue),Z.updateRenderTargetMipmap(Ue),bt.has("WEBGL_multisampled_render_to_texture")===!1){let Ve=!1;for(let ft=0,Yt=W.length;ft<Yt;ft++){const Zt=W[ft],{object:Ct,geometry:gn,material:je,group:On}=Zt;if(je.side===Sa&&Ct.layers.test(oe.layers)){const at=je.side;je.side=Zn,je.needsUpdate=!0,Qi(Ct,ce,oe,gn,je,On),je.side=at,je.needsUpdate=!0,Ve=!0}}Ve===!0&&(Z.updateMultisampleRenderTarget(Ue),Z.updateRenderTargetMipmap(Ue))}L.setRenderTarget(Le,We,Ke),L.setClearColor(Q,de),rt!==void 0&&(oe.viewport=rt),L.toneMapping=nt}function mn(N,W,ce){const oe=W.isScene===!0?W.overrideMaterial:null;for(let te=0,Ue=N.length;te<Ue;te++){const Be=N[te],{object:Le,geometry:We,group:Ke}=Be;let nt=Be.material;nt.allowOverride===!0&&oe!==null&&(nt=oe),Le.layers.test(ce.layers)&&Qi(Le,W,ce,We,nt,Ke)}}function Qi(N,W,ce,oe,te,Ue){N.onBeforeRender(L,W,ce,oe,te,Ue),N.modelViewMatrix.multiplyMatrices(ce.matrixWorldInverse,N.matrixWorld),N.normalMatrix.getNormalMatrix(N.modelViewMatrix),te.onBeforeRender(L,W,ce,oe,N,Ue),te.transparent===!0&&te.side===Sa&&te.forceSinglePass===!1?(te.side=Zn,te.needsUpdate=!0,L.renderBufferDirect(ce,W,oe,te,N,Ue),te.side=ds,te.needsUpdate=!0,L.renderBufferDirect(ce,W,oe,te,N,Ue),te.side=Sa):L.renderBufferDirect(ce,W,oe,te,N,Ue),N.onAfterRender(L,W,ce,oe,te,Ue)}function Ua(N,W,ce){W.isScene!==!0&&(W=Nt);const oe=b.get(N),te=V.state.lights,Ue=V.state.shadowsArray,Be=te.state.version,Le=De.getParameters(N,te.state,Ue,W,ce),We=De.getProgramCacheKey(Le);let Ke=oe.programs;oe.environment=N.isMeshStandardMaterial||N.isMeshLambertMaterial||N.isMeshPhongMaterial?W.environment:null,oe.fog=W.fog;const nt=N.isMeshStandardMaterial||N.isMeshLambertMaterial&&!N.envMap||N.isMeshPhongMaterial&&!N.envMap;oe.envMap=xe.get(N.envMap||oe.environment,nt),oe.envMapRotation=oe.environment!==null&&N.envMap===null?W.environmentRotation:N.envMapRotation,Ke===void 0&&(N.addEventListener("dispose",Tt),Ke=new Map,oe.programs=Ke);let rt=Ke.get(We);if(rt!==void 0){if(oe.currentProgram===rt&&oe.lightsStateVersion===Be)return vl(N,Le),rt}else Le.uniforms=De.getUniforms(N),N.onBeforeCompile(Le,L),rt=De.acquireProgram(Le,We),Ke.set(We,rt),oe.uniforms=Le.uniforms;const Ve=oe.uniforms;return(!N.isShaderMaterial&&!N.isRawShaderMaterial||N.clipping===!0)&&(Ve.clippingPlanes=be.uniform),vl(N,Le),oe.needsLights=no(N),oe.lightsStateVersion=Be,oe.needsLights&&(Ve.ambientLightColor.value=te.state.ambient,Ve.lightProbe.value=te.state.probe,Ve.directionalLights.value=te.state.directional,Ve.directionalLightShadows.value=te.state.directionalShadow,Ve.spotLights.value=te.state.spot,Ve.spotLightShadows.value=te.state.spotShadow,Ve.rectAreaLights.value=te.state.rectArea,Ve.ltc_1.value=te.state.rectAreaLTC1,Ve.ltc_2.value=te.state.rectAreaLTC2,Ve.pointLights.value=te.state.point,Ve.pointLightShadows.value=te.state.pointShadow,Ve.hemisphereLights.value=te.state.hemi,Ve.directionalShadowMatrix.value=te.state.directionalShadowMatrix,Ve.spotLightMatrix.value=te.state.spotLightMatrix,Ve.spotLightMap.value=te.state.spotLightMap,Ve.pointShadowMatrix.value=te.state.pointShadowMatrix),oe.currentProgram=rt,oe.uniformsList=null,rt}function _l(N){if(N.uniformsList===null){const W=N.currentProgram.getUniforms();N.uniformsList=uu.seqWithValue(W.seq,N.uniforms)}return N.uniformsList}function vl(N,W){const ce=b.get(N);ce.outputColorSpace=W.outputColorSpace,ce.batching=W.batching,ce.batchingColor=W.batchingColor,ce.instancing=W.instancing,ce.instancingColor=W.instancingColor,ce.instancingMorph=W.instancingMorph,ce.skinning=W.skinning,ce.morphTargets=W.morphTargets,ce.morphNormals=W.morphNormals,ce.morphColors=W.morphColors,ce.morphTargetsCount=W.morphTargetsCount,ce.numClippingPlanes=W.numClippingPlanes,ce.numIntersection=W.numClipIntersection,ce.vertexAlphas=W.vertexAlphas,ce.vertexTangents=W.vertexTangents,ce.toneMapping=W.toneMapping}function xl(N,W,ce,oe,te){W.isScene!==!0&&(W=Nt),Z.resetTextureUnits();const Ue=W.fog,Be=oe.isMeshStandardMaterial||oe.isMeshLambertMaterial||oe.isMeshPhongMaterial?W.environment:null,Le=re===null?L.outputColorSpace:re.isXRRenderTarget===!0?re.texture.colorSpace:Zr,We=oe.isMeshStandardMaterial||oe.isMeshLambertMaterial&&!oe.envMap||oe.isMeshPhongMaterial&&!oe.envMap,Ke=xe.get(oe.envMap||Be,We),nt=oe.vertexColors===!0&&!!ce.attributes.color&&ce.attributes.color.itemSize===4,rt=!!ce.attributes.tangent&&(!!oe.normalMap||oe.anisotropy>0),Ve=!!ce.morphAttributes.position,ft=!!ce.morphAttributes.normal,Yt=!!ce.morphAttributes.color;let Zt=qi;oe.toneMapped&&(re===null||re.isXRRenderTarget===!0)&&(Zt=L.toneMapping);const Ct=ce.morphAttributes.position||ce.morphAttributes.normal||ce.morphAttributes.color,gn=Ct!==void 0?Ct.length:0,je=b.get(oe),On=V.state.lights;if(Qe===!0&&(qe===!0||N!==ee)){const cn=N===ee&&oe.id===fe;be.setState(oe,N,cn)}let at=!1;oe.version===je.__version?(je.needsLights&&je.lightsStateVersion!==On.state.version||je.outputColorSpace!==Le||te.isBatchedMesh&&je.batching===!1||!te.isBatchedMesh&&je.batching===!0||te.isBatchedMesh&&je.batchingColor===!0&&te.colorTexture===null||te.isBatchedMesh&&je.batchingColor===!1&&te.colorTexture!==null||te.isInstancedMesh&&je.instancing===!1||!te.isInstancedMesh&&je.instancing===!0||te.isSkinnedMesh&&je.skinning===!1||!te.isSkinnedMesh&&je.skinning===!0||te.isInstancedMesh&&je.instancingColor===!0&&te.instanceColor===null||te.isInstancedMesh&&je.instancingColor===!1&&te.instanceColor!==null||te.isInstancedMesh&&je.instancingMorph===!0&&te.morphTexture===null||te.isInstancedMesh&&je.instancingMorph===!1&&te.morphTexture!==null||je.envMap!==Ke||oe.fog===!0&&je.fog!==Ue||je.numClippingPlanes!==void 0&&(je.numClippingPlanes!==be.numPlanes||je.numIntersection!==be.numIntersection)||je.vertexAlphas!==nt||je.vertexTangents!==rt||je.morphTargets!==Ve||je.morphNormals!==ft||je.morphColors!==Yt||je.toneMapping!==Zt||je.morphTargetsCount!==gn)&&(at=!0):(at=!0,je.__version=oe.version);let Pn=je.currentProgram;at===!0&&(Pn=Ua(oe,W,te));let Qn=!1,bi=!1,Jn=!1;const Pt=Pn.getUniforms(),ln=je.uniforms;if(Ye.useProgram(Pn.program)&&(Qn=!0,bi=!0,Jn=!0),oe.id!==fe&&(fe=oe.id,bi=!0),Qn||ee!==N){Ye.buffers.depth.getReversed()&&N.reversedDepth!==!0&&(N._reversedDepth=!0,N.updateProjectionMatrix()),Pt.setValue(k,"projectionMatrix",N.projectionMatrix),Pt.setValue(k,"viewMatrix",N.matrixWorldInverse);const Ti=Pt.map.cameraPosition;Ti!==void 0&&Ti.setValue(k,yt.setFromMatrixPosition(N.matrixWorld)),Ot.logarithmicDepthBuffer&&Pt.setValue(k,"logDepthBufFC",2/(Math.log(N.far+1)/Math.LN2)),(oe.isMeshPhongMaterial||oe.isMeshToonMaterial||oe.isMeshLambertMaterial||oe.isMeshBasicMaterial||oe.isMeshStandardMaterial||oe.isShaderMaterial)&&Pt.setValue(k,"isOrthographic",N.isOrthographicCamera===!0),ee!==N&&(ee=N,bi=!0,Jn=!0)}if(je.needsLights&&(On.state.directionalShadowMap.length>0&&Pt.setValue(k,"directionalShadowMap",On.state.directionalShadowMap,Z),On.state.spotShadowMap.length>0&&Pt.setValue(k,"spotShadowMap",On.state.spotShadowMap,Z),On.state.pointShadowMap.length>0&&Pt.setValue(k,"pointShadowMap",On.state.pointShadowMap,Z)),te.isSkinnedMesh){Pt.setOptional(k,te,"bindMatrix"),Pt.setOptional(k,te,"bindMatrixInverse");const cn=te.skeleton;cn&&(cn.boneTexture===null&&cn.computeBoneTexture(),Pt.setValue(k,"boneTexture",cn.boneTexture,Z))}te.isBatchedMesh&&(Pt.setOptional(k,te,"batchingTexture"),Pt.setValue(k,"batchingTexture",te._matricesTexture,Z),Pt.setOptional(k,te,"batchingIdTexture"),Pt.setValue(k,"batchingIdTexture",te._indirectTexture,Z),Pt.setOptional(k,te,"batchingColorTexture"),te._colorsTexture!==null&&Pt.setValue(k,"batchingColorTexture",te._colorsTexture,Z));const Fn=ce.morphAttributes;if((Fn.position!==void 0||Fn.normal!==void 0||Fn.color!==void 0)&&Ie.update(te,ce,Pn),(bi||je.receiveShadow!==te.receiveShadow)&&(je.receiveShadow=te.receiveShadow,Pt.setValue(k,"receiveShadow",te.receiveShadow)),(oe.isMeshStandardMaterial||oe.isMeshLambertMaterial||oe.isMeshPhongMaterial)&&oe.envMap===null&&W.environment!==null&&(ln.envMapIntensity.value=W.environmentIntensity),ln.dfgLUT!==void 0&&(ln.dfgLUT.value=s3()),bi&&(Pt.setValue(k,"toneMappingExposure",L.toneMappingExposure),je.needsLights&&gs(ln,Jn),Ue&&oe.fog===!0&&Je.refreshFogUniforms(ln,Ue),Je.refreshMaterialUniforms(ln,oe,ve,j,V.state.transmissionRenderTarget[N.id]),uu.upload(k,_l(je),ln,Z)),oe.isShaderMaterial&&oe.uniformsNeedUpdate===!0&&(uu.upload(k,_l(je),ln,Z),oe.uniformsNeedUpdate=!1),oe.isSpriteMaterial&&Pt.setValue(k,"center",te.center),Pt.setValue(k,"modelViewMatrix",te.modelViewMatrix),Pt.setValue(k,"normalMatrix",te.normalMatrix),Pt.setValue(k,"modelMatrix",te.matrixWorld),oe.isShaderMaterial||oe.isRawShaderMaterial){const cn=oe.uniformsGroups;for(let Ti=0,Ji=cn.length;Ti<Ji;Ti++){const Ks=cn[Ti];ze.update(Ks,Pn),ze.bind(Ks,Pn)}}return Pn}function gs(N,W){N.ambientLightColor.needsUpdate=W,N.lightProbe.needsUpdate=W,N.directionalLights.needsUpdate=W,N.directionalLightShadows.needsUpdate=W,N.pointLights.needsUpdate=W,N.pointLightShadows.needsUpdate=W,N.spotLights.needsUpdate=W,N.spotLightShadows.needsUpdate=W,N.rectAreaLights.needsUpdate=W,N.hemisphereLights.needsUpdate=W}function no(N){return N.isMeshLambertMaterial||N.isMeshToonMaterial||N.isMeshPhongMaterial||N.isMeshStandardMaterial||N.isShadowMaterial||N.isShaderMaterial&&N.lights===!0}this.getActiveCubeFace=function(){return w},this.getActiveMipmapLevel=function(){return Y},this.getRenderTarget=function(){return re},this.setRenderTargetTextures=function(N,W,ce){const oe=b.get(N);oe.__autoAllocateDepthBuffer=N.resolveDepthBuffer===!1,oe.__autoAllocateDepthBuffer===!1&&(oe.__useRenderToTexture=!1),b.get(N.texture).__webglTexture=W,b.get(N.depthTexture).__webglTexture=oe.__autoAllocateDepthBuffer?void 0:ce,oe.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(N,W){const ce=b.get(N);ce.__webglFramebuffer=W,ce.__useDefaultFramebuffer=W===void 0};const La=k.createFramebuffer();this.setRenderTarget=function(N,W=0,ce=0){re=N,w=W,Y=ce;let oe=null,te=!1,Ue=!1;if(N){const Le=b.get(N);if(Le.__useDefaultFramebuffer!==void 0){Ye.bindFramebuffer(k.FRAMEBUFFER,Le.__webglFramebuffer),I.copy(N.viewport),B.copy(N.scissor),$=N.scissorTest,Ye.viewport(I),Ye.scissor(B),Ye.setScissorTest($),fe=-1;return}else if(Le.__webglFramebuffer===void 0)Z.setupRenderTarget(N);else if(Le.__hasExternalTextures)Z.rebindTextures(N,b.get(N.texture).__webglTexture,b.get(N.depthTexture).__webglTexture);else if(N.depthBuffer){const nt=N.depthTexture;if(Le.__boundDepthTexture!==nt){if(nt!==null&&b.has(nt)&&(N.width!==nt.image.width||N.height!==nt.image.height))throw new Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");Z.setupDepthRenderbuffer(N)}}const We=N.texture;(We.isData3DTexture||We.isDataArrayTexture||We.isCompressedArrayTexture)&&(Ue=!0);const Ke=b.get(N).__webglFramebuffer;N.isWebGLCubeRenderTarget?(Array.isArray(Ke[W])?oe=Ke[W][ce]:oe=Ke[W],te=!0):N.samples>0&&Z.useMultisampledRTT(N)===!1?oe=b.get(N).__webglMultisampledFramebuffer:Array.isArray(Ke)?oe=Ke[ce]:oe=Ke,I.copy(N.viewport),B.copy(N.scissor),$=N.scissorTest}else I.copy(ie).multiplyScalar(ve).floor(),B.copy(Se).multiplyScalar(ve).floor(),$=Ae;if(ce!==0&&(oe=La),Ye.bindFramebuffer(k.FRAMEBUFFER,oe)&&Ye.drawBuffers(N,oe),Ye.viewport(I),Ye.scissor(B),Ye.setScissorTest($),te){const Le=b.get(N.texture);k.framebufferTexture2D(k.FRAMEBUFFER,k.COLOR_ATTACHMENT0,k.TEXTURE_CUBE_MAP_POSITIVE_X+W,Le.__webglTexture,ce)}else if(Ue){const Le=W;for(let We=0;We<N.textures.length;We++){const Ke=b.get(N.textures[We]);k.framebufferTextureLayer(k.FRAMEBUFFER,k.COLOR_ATTACHMENT0+We,Ke.__webglTexture,ce,Le)}}else if(N!==null&&ce!==0){const Le=b.get(N.texture);k.framebufferTexture2D(k.FRAMEBUFFER,k.COLOR_ATTACHMENT0,k.TEXTURE_2D,Le.__webglTexture,ce)}fe=-1},this.readRenderTargetPixels=function(N,W,ce,oe,te,Ue,Be,Le=0){if(!(N&&N.isWebGLRenderTarget)){At("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let We=b.get(N).__webglFramebuffer;if(N.isWebGLCubeRenderTarget&&Be!==void 0&&(We=We[Be]),We){Ye.bindFramebuffer(k.FRAMEBUFFER,We);try{const Ke=N.textures[Le],nt=Ke.format,rt=Ke.type;if(N.textures.length>1&&k.readBuffer(k.COLOR_ATTACHMENT0+Le),!Ot.textureFormatReadable(nt)){At("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!Ot.textureTypeReadable(rt)){At("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}W>=0&&W<=N.width-oe&&ce>=0&&ce<=N.height-te&&k.readPixels(W,ce,oe,te,we.convert(nt),we.convert(rt),Ue)}finally{const Ke=re!==null?b.get(re).__webglFramebuffer:null;Ye.bindFramebuffer(k.FRAMEBUFFER,Ke)}}},this.readRenderTargetPixelsAsync=async function(N,W,ce,oe,te,Ue,Be,Le=0){if(!(N&&N.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let We=b.get(N).__webglFramebuffer;if(N.isWebGLCubeRenderTarget&&Be!==void 0&&(We=We[Be]),We)if(W>=0&&W<=N.width-oe&&ce>=0&&ce<=N.height-te){Ye.bindFramebuffer(k.FRAMEBUFFER,We);const Ke=N.textures[Le],nt=Ke.format,rt=Ke.type;if(N.textures.length>1&&k.readBuffer(k.COLOR_ATTACHMENT0+Le),!Ot.textureFormatReadable(nt))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!Ot.textureTypeReadable(rt))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");const Ve=k.createBuffer();k.bindBuffer(k.PIXEL_PACK_BUFFER,Ve),k.bufferData(k.PIXEL_PACK_BUFFER,Ue.byteLength,k.STREAM_READ),k.readPixels(W,ce,oe,te,we.convert(nt),we.convert(rt),0);const ft=re!==null?b.get(re).__webglFramebuffer:null;Ye.bindFramebuffer(k.FRAMEBUFFER,ft);const Yt=k.fenceSync(k.SYNC_GPU_COMMANDS_COMPLETE,0);return k.flush(),await Rb(k,Yt,4),k.bindBuffer(k.PIXEL_PACK_BUFFER,Ve),k.getBufferSubData(k.PIXEL_PACK_BUFFER,0,Ue),k.deleteBuffer(Ve),k.deleteSync(Yt),Ue}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(N,W=null,ce=0){const oe=Math.pow(2,-ce),te=Math.floor(N.image.width*oe),Ue=Math.floor(N.image.height*oe),Be=W!==null?W.x:0,Le=W!==null?W.y:0;Z.setTexture2D(N,0),k.copyTexSubImage2D(k.TEXTURE_2D,ce,0,0,Be,Le,te,Ue),Ye.unbindTexture()};const Oa=k.createFramebuffer(),_s=k.createFramebuffer();this.copyTextureToTexture=function(N,W,ce=null,oe=null,te=0,Ue=0){let Be,Le,We,Ke,nt,rt,Ve,ft,Yt;const Zt=N.isCompressedTexture?N.mipmaps[Ue]:N.image;if(ce!==null)Be=ce.max.x-ce.min.x,Le=ce.max.y-ce.min.y,We=ce.isBox3?ce.max.z-ce.min.z:1,Ke=ce.min.x,nt=ce.min.y,rt=ce.isBox3?ce.min.z:0;else{const ln=Math.pow(2,-te);Be=Math.floor(Zt.width*ln),Le=Math.floor(Zt.height*ln),N.isDataArrayTexture?We=Zt.depth:N.isData3DTexture?We=Math.floor(Zt.depth*ln):We=1,Ke=0,nt=0,rt=0}oe!==null?(Ve=oe.x,ft=oe.y,Yt=oe.z):(Ve=0,ft=0,Yt=0);const Ct=we.convert(W.format),gn=we.convert(W.type);let je;W.isData3DTexture?(Z.setTexture3D(W,0),je=k.TEXTURE_3D):W.isDataArrayTexture||W.isCompressedArrayTexture?(Z.setTexture2DArray(W,0),je=k.TEXTURE_2D_ARRAY):(Z.setTexture2D(W,0),je=k.TEXTURE_2D),k.pixelStorei(k.UNPACK_FLIP_Y_WEBGL,W.flipY),k.pixelStorei(k.UNPACK_PREMULTIPLY_ALPHA_WEBGL,W.premultiplyAlpha),k.pixelStorei(k.UNPACK_ALIGNMENT,W.unpackAlignment);const On=k.getParameter(k.UNPACK_ROW_LENGTH),at=k.getParameter(k.UNPACK_IMAGE_HEIGHT),Pn=k.getParameter(k.UNPACK_SKIP_PIXELS),Qn=k.getParameter(k.UNPACK_SKIP_ROWS),bi=k.getParameter(k.UNPACK_SKIP_IMAGES);k.pixelStorei(k.UNPACK_ROW_LENGTH,Zt.width),k.pixelStorei(k.UNPACK_IMAGE_HEIGHT,Zt.height),k.pixelStorei(k.UNPACK_SKIP_PIXELS,Ke),k.pixelStorei(k.UNPACK_SKIP_ROWS,nt),k.pixelStorei(k.UNPACK_SKIP_IMAGES,rt);const Jn=N.isDataArrayTexture||N.isData3DTexture,Pt=W.isDataArrayTexture||W.isData3DTexture;if(N.isDepthTexture){const ln=b.get(N),Fn=b.get(W),cn=b.get(ln.__renderTarget),Ti=b.get(Fn.__renderTarget);Ye.bindFramebuffer(k.READ_FRAMEBUFFER,cn.__webglFramebuffer),Ye.bindFramebuffer(k.DRAW_FRAMEBUFFER,Ti.__webglFramebuffer);for(let Ji=0;Ji<We;Ji++)Jn&&(k.framebufferTextureLayer(k.READ_FRAMEBUFFER,k.COLOR_ATTACHMENT0,b.get(N).__webglTexture,te,rt+Ji),k.framebufferTextureLayer(k.DRAW_FRAMEBUFFER,k.COLOR_ATTACHMENT0,b.get(W).__webglTexture,Ue,Yt+Ji)),k.blitFramebuffer(Ke,nt,Be,Le,Ve,ft,Be,Le,k.DEPTH_BUFFER_BIT,k.NEAREST);Ye.bindFramebuffer(k.READ_FRAMEBUFFER,null),Ye.bindFramebuffer(k.DRAW_FRAMEBUFFER,null)}else if(te!==0||N.isRenderTargetTexture||b.has(N)){const ln=b.get(N),Fn=b.get(W);Ye.bindFramebuffer(k.READ_FRAMEBUFFER,Oa),Ye.bindFramebuffer(k.DRAW_FRAMEBUFFER,_s);for(let cn=0;cn<We;cn++)Jn?k.framebufferTextureLayer(k.READ_FRAMEBUFFER,k.COLOR_ATTACHMENT0,ln.__webglTexture,te,rt+cn):k.framebufferTexture2D(k.READ_FRAMEBUFFER,k.COLOR_ATTACHMENT0,k.TEXTURE_2D,ln.__webglTexture,te),Pt?k.framebufferTextureLayer(k.DRAW_FRAMEBUFFER,k.COLOR_ATTACHMENT0,Fn.__webglTexture,Ue,Yt+cn):k.framebufferTexture2D(k.DRAW_FRAMEBUFFER,k.COLOR_ATTACHMENT0,k.TEXTURE_2D,Fn.__webglTexture,Ue),te!==0?k.blitFramebuffer(Ke,nt,Be,Le,Ve,ft,Be,Le,k.COLOR_BUFFER_BIT,k.NEAREST):Pt?k.copyTexSubImage3D(je,Ue,Ve,ft,Yt+cn,Ke,nt,Be,Le):k.copyTexSubImage2D(je,Ue,Ve,ft,Ke,nt,Be,Le);Ye.bindFramebuffer(k.READ_FRAMEBUFFER,null),Ye.bindFramebuffer(k.DRAW_FRAMEBUFFER,null)}else Pt?N.isDataTexture||N.isData3DTexture?k.texSubImage3D(je,Ue,Ve,ft,Yt,Be,Le,We,Ct,gn,Zt.data):W.isCompressedArrayTexture?k.compressedTexSubImage3D(je,Ue,Ve,ft,Yt,Be,Le,We,Ct,Zt.data):k.texSubImage3D(je,Ue,Ve,ft,Yt,Be,Le,We,Ct,gn,Zt):N.isDataTexture?k.texSubImage2D(k.TEXTURE_2D,Ue,Ve,ft,Be,Le,Ct,gn,Zt.data):N.isCompressedTexture?k.compressedTexSubImage2D(k.TEXTURE_2D,Ue,Ve,ft,Zt.width,Zt.height,Ct,Zt.data):k.texSubImage2D(k.TEXTURE_2D,Ue,Ve,ft,Be,Le,Ct,gn,Zt);k.pixelStorei(k.UNPACK_ROW_LENGTH,On),k.pixelStorei(k.UNPACK_IMAGE_HEIGHT,at),k.pixelStorei(k.UNPACK_SKIP_PIXELS,Pn),k.pixelStorei(k.UNPACK_SKIP_ROWS,Qn),k.pixelStorei(k.UNPACK_SKIP_IMAGES,bi),Ue===0&&W.generateMipmaps&&k.generateMipmap(je),Ye.unbindTexture()},this.initRenderTarget=function(N){b.get(N).__webglFramebuffer===void 0&&Z.setupRenderTarget(N)},this.initTexture=function(N){N.isCubeTexture?Z.setTextureCube(N,0):N.isData3DTexture?Z.setTexture3D(N,0):N.isDataArrayTexture||N.isCompressedArrayTexture?Z.setTexture2DArray(N,0):Z.setTexture2D(N,0),Ye.unbindTexture()},this.resetState=function(){w=0,Y=0,re=null,Ye.reset(),Ce.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return Wi}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;const i=this.getContext();i.drawingBufferColorSpace=Rt._getDrawingBufferColorSpace(e),i.unpackColorSpace=Rt._getUnpackColorSpace()}}const wv={type:"change"},Lp={type:"start"},Lx={type:"end"},tu=new yu,Dv=new us,o3=Math.cos(70*Db.DEG2RAD),vn=new se,qn=2*Math.PI,kt={NONE:-1,ROTATE:0,DOLLY:1,PAN:2,TOUCH_ROTATE:3,TOUCH_PAN:4,TOUCH_DOLLY_PAN:5,TOUCH_DOLLY_ROTATE:6},md=1e-6;class l3 extends hT{constructor(e,i=null){super(e,i),this.state=kt.NONE,this.target=new se,this.cursor=new se,this.minDistance=0,this.maxDistance=1/0,this.minZoom=0,this.maxZoom=1/0,this.minTargetRadius=0,this.maxTargetRadius=1/0,this.minPolarAngle=0,this.maxPolarAngle=Math.PI,this.minAzimuthAngle=-1/0,this.maxAzimuthAngle=1/0,this.enableDamping=!1,this.dampingFactor=.05,this.enableZoom=!0,this.zoomSpeed=1,this.enableRotate=!0,this.rotateSpeed=1,this.keyRotateSpeed=1,this.enablePan=!0,this.panSpeed=1,this.screenSpacePanning=!0,this.keyPanSpeed=7,this.zoomToCursor=!1,this.autoRotate=!1,this.autoRotateSpeed=2,this.keys={LEFT:"ArrowLeft",UP:"ArrowUp",RIGHT:"ArrowRight",BOTTOM:"ArrowDown"},this.mouseButtons={LEFT:kr.ROTATE,MIDDLE:kr.DOLLY,RIGHT:kr.PAN},this.touches={ONE:Vr.ROTATE,TWO:Vr.DOLLY_PAN},this.target0=this.target.clone(),this.position0=this.object.position.clone(),this.zoom0=this.object.zoom,this._cursorStyle="auto",this._domElementKeyEvents=null,this._lastPosition=new se,this._lastQuaternion=new ps,this._lastTargetPosition=new se,this._quat=new ps().setFromUnitVectors(e.up,new se(0,1,0)),this._quatInverse=this._quat.clone().invert(),this._spherical=new av,this._sphericalDelta=new av,this._scale=1,this._panOffset=new se,this._rotateStart=new mt,this._rotateEnd=new mt,this._rotateDelta=new mt,this._panStart=new mt,this._panEnd=new mt,this._panDelta=new mt,this._dollyStart=new mt,this._dollyEnd=new mt,this._dollyDelta=new mt,this._dollyDirection=new se,this._mouse=new mt,this._performCursorZoom=!1,this._pointers=[],this._pointerPositions={},this._controlActive=!1,this._onPointerMove=u3.bind(this),this._onPointerDown=c3.bind(this),this._onPointerUp=f3.bind(this),this._onContextMenu=v3.bind(this),this._onMouseWheel=p3.bind(this),this._onKeyDown=m3.bind(this),this._onTouchStart=g3.bind(this),this._onTouchMove=_3.bind(this),this._onMouseDown=h3.bind(this),this._onMouseMove=d3.bind(this),this._interceptControlDown=x3.bind(this),this._interceptControlUp=y3.bind(this),this.domElement!==null&&this.connect(this.domElement),this.update()}set cursorStyle(e){this._cursorStyle=e,e==="grab"?this.domElement.style.cursor="grab":this.domElement.style.cursor="auto"}get cursorStyle(){return this._cursorStyle}connect(e){super.connect(e),this.domElement.addEventListener("pointerdown",this._onPointerDown),this.domElement.addEventListener("pointercancel",this._onPointerUp),this.domElement.addEventListener("contextmenu",this._onContextMenu),this.domElement.addEventListener("wheel",this._onMouseWheel,{passive:!1}),this.domElement.getRootNode().addEventListener("keydown",this._interceptControlDown,{passive:!0,capture:!0}),this.domElement.style.touchAction="none"}disconnect(){this.domElement.removeEventListener("pointerdown",this._onPointerDown),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.domElement.removeEventListener("pointercancel",this._onPointerUp),this.domElement.removeEventListener("wheel",this._onMouseWheel),this.domElement.removeEventListener("contextmenu",this._onContextMenu),this.stopListenToKeyEvents(),this.domElement.getRootNode().removeEventListener("keydown",this._interceptControlDown,{capture:!0}),this.domElement.style.touchAction="auto"}dispose(){this.disconnect()}getPolarAngle(){return this._spherical.phi}getAzimuthalAngle(){return this._spherical.theta}getDistance(){return this.object.position.distanceTo(this.target)}listenToKeyEvents(e){e.addEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=e}stopListenToKeyEvents(){this._domElementKeyEvents!==null&&(this._domElementKeyEvents.removeEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=null)}saveState(){this.target0.copy(this.target),this.position0.copy(this.object.position),this.zoom0=this.object.zoom}reset(){this.target.copy(this.target0),this.object.position.copy(this.position0),this.object.zoom=this.zoom0,this.object.updateProjectionMatrix(),this.dispatchEvent(wv),this.update(),this.state=kt.NONE}pan(e,i){this._pan(e,i),this.update()}dollyIn(e){this._dollyIn(e),this.update()}dollyOut(e){this._dollyOut(e),this.update()}rotateLeft(e){this._rotateLeft(e),this.update()}rotateUp(e){this._rotateUp(e),this.update()}update(e=null){const i=this.object.position;vn.copy(i).sub(this.target),vn.applyQuaternion(this._quat),this._spherical.setFromVector3(vn),this.autoRotate&&this.state===kt.NONE&&this._rotateLeft(this._getAutoRotationAngle(e)),this.enableDamping?(this._spherical.theta+=this._sphericalDelta.theta*this.dampingFactor,this._spherical.phi+=this._sphericalDelta.phi*this.dampingFactor):(this._spherical.theta+=this._sphericalDelta.theta,this._spherical.phi+=this._sphericalDelta.phi);let r=this.minAzimuthAngle,l=this.maxAzimuthAngle;isFinite(r)&&isFinite(l)&&(r<-Math.PI?r+=qn:r>Math.PI&&(r-=qn),l<-Math.PI?l+=qn:l>Math.PI&&(l-=qn),r<=l?this._spherical.theta=Math.max(r,Math.min(l,this._spherical.theta)):this._spherical.theta=this._spherical.theta>(r+l)/2?Math.max(r,this._spherical.theta):Math.min(l,this._spherical.theta)),this._spherical.phi=Math.max(this.minPolarAngle,Math.min(this.maxPolarAngle,this._spherical.phi)),this._spherical.makeSafe(),this.enableDamping===!0?this.target.addScaledVector(this._panOffset,this.dampingFactor):this.target.add(this._panOffset),this.target.sub(this.cursor),this.target.clampLength(this.minTargetRadius,this.maxTargetRadius),this.target.add(this.cursor);let c=!1;if(this.zoomToCursor&&this._performCursorZoom||this.object.isOrthographicCamera)this._spherical.radius=this._clampDistance(this._spherical.radius);else{const f=this._spherical.radius;this._spherical.radius=this._clampDistance(this._spherical.radius*this._scale),c=f!=this._spherical.radius}if(vn.setFromSpherical(this._spherical),vn.applyQuaternion(this._quatInverse),i.copy(this.target).add(vn),this.object.lookAt(this.target),this.enableDamping===!0?(this._sphericalDelta.theta*=1-this.dampingFactor,this._sphericalDelta.phi*=1-this.dampingFactor,this._panOffset.multiplyScalar(1-this.dampingFactor)):(this._sphericalDelta.set(0,0,0),this._panOffset.set(0,0,0)),this.zoomToCursor&&this._performCursorZoom){let f=null;if(this.object.isPerspectiveCamera){const p=vn.length();f=this._clampDistance(p*this._scale);const m=p-f;this.object.position.addScaledVector(this._dollyDirection,m),this.object.updateMatrixWorld(),c=!!m}else if(this.object.isOrthographicCamera){const p=new se(this._mouse.x,this._mouse.y,0);p.unproject(this.object);const m=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),this.object.updateProjectionMatrix(),c=m!==this.object.zoom;const d=new se(this._mouse.x,this._mouse.y,0);d.unproject(this.object),this.object.position.sub(d).add(p),this.object.updateMatrixWorld(),f=vn.length()}else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - zoom to cursor disabled."),this.zoomToCursor=!1;f!==null&&(this.screenSpacePanning?this.target.set(0,0,-1).transformDirection(this.object.matrix).multiplyScalar(f).add(this.object.position):(tu.origin.copy(this.object.position),tu.direction.set(0,0,-1).transformDirection(this.object.matrix),Math.abs(this.object.up.dot(tu.direction))<o3?this.object.lookAt(this.target):(Dv.setFromNormalAndCoplanarPoint(this.object.up,this.target),tu.intersectPlane(Dv,this.target))))}else if(this.object.isOrthographicCamera){const f=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),f!==this.object.zoom&&(this.object.updateProjectionMatrix(),c=!0)}return this._scale=1,this._performCursorZoom=!1,c||this._lastPosition.distanceToSquared(this.object.position)>md||8*(1-this._lastQuaternion.dot(this.object.quaternion))>md||this._lastTargetPosition.distanceToSquared(this.target)>md?(this.dispatchEvent(wv),this._lastPosition.copy(this.object.position),this._lastQuaternion.copy(this.object.quaternion),this._lastTargetPosition.copy(this.target),!0):!1}_getAutoRotationAngle(e){return e!==null?qn/60*this.autoRotateSpeed*e:qn/60/60*this.autoRotateSpeed}_getZoomScale(e){const i=Math.abs(e*.01);return Math.pow(.95,this.zoomSpeed*i)}_rotateLeft(e){this._sphericalDelta.theta-=e}_rotateUp(e){this._sphericalDelta.phi-=e}_panLeft(e,i){vn.setFromMatrixColumn(i,0),vn.multiplyScalar(-e),this._panOffset.add(vn)}_panUp(e,i){this.screenSpacePanning===!0?vn.setFromMatrixColumn(i,1):(vn.setFromMatrixColumn(i,0),vn.crossVectors(this.object.up,vn)),vn.multiplyScalar(e),this._panOffset.add(vn)}_pan(e,i){const r=this.domElement;if(this.object.isPerspectiveCamera){const l=this.object.position;vn.copy(l).sub(this.target);let c=vn.length();c*=Math.tan(this.object.fov/2*Math.PI/180),this._panLeft(2*e*c/r.clientHeight,this.object.matrix),this._panUp(2*i*c/r.clientHeight,this.object.matrix)}else this.object.isOrthographicCamera?(this._panLeft(e*(this.object.right-this.object.left)/this.object.zoom/r.clientWidth,this.object.matrix),this._panUp(i*(this.object.top-this.object.bottom)/this.object.zoom/r.clientHeight,this.object.matrix)):(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - pan disabled."),this.enablePan=!1)}_dollyOut(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale/=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_dollyIn(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale*=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_updateZoomParameters(e,i){if(!this.zoomToCursor)return;this._performCursorZoom=!0;const r=this.domElement.getBoundingClientRect(),l=e-r.left,c=i-r.top,f=r.width,p=r.height;this._mouse.x=l/f*2-1,this._mouse.y=-(c/p)*2+1,this._dollyDirection.set(this._mouse.x,this._mouse.y,1).unproject(this.object).sub(this.object.position).normalize()}_clampDistance(e){return Math.max(this.minDistance,Math.min(this.maxDistance,e))}_handleMouseDownRotate(e){this._rotateStart.set(e.clientX,e.clientY)}_handleMouseDownDolly(e){this._updateZoomParameters(e.clientX,e.clientX),this._dollyStart.set(e.clientX,e.clientY)}_handleMouseDownPan(e){this._panStart.set(e.clientX,e.clientY)}_handleMouseMoveRotate(e){this._rotateEnd.set(e.clientX,e.clientY),this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const i=this.domElement;this._rotateLeft(qn*this._rotateDelta.x/i.clientHeight),this._rotateUp(qn*this._rotateDelta.y/i.clientHeight),this._rotateStart.copy(this._rotateEnd),this.update()}_handleMouseMoveDolly(e){this._dollyEnd.set(e.clientX,e.clientY),this._dollyDelta.subVectors(this._dollyEnd,this._dollyStart),this._dollyDelta.y>0?this._dollyOut(this._getZoomScale(this._dollyDelta.y)):this._dollyDelta.y<0&&this._dollyIn(this._getZoomScale(this._dollyDelta.y)),this._dollyStart.copy(this._dollyEnd),this.update()}_handleMouseMovePan(e){this._panEnd.set(e.clientX,e.clientY),this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd),this.update()}_handleMouseWheel(e){this._updateZoomParameters(e.clientX,e.clientY),e.deltaY<0?this._dollyIn(this._getZoomScale(e.deltaY)):e.deltaY>0&&this._dollyOut(this._getZoomScale(e.deltaY)),this.update()}_handleKeyDown(e){let i=!1;switch(e.code){case this.keys.UP:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(qn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,this.keyPanSpeed),i=!0;break;case this.keys.BOTTOM:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(-qn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,-this.keyPanSpeed),i=!0;break;case this.keys.LEFT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(qn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(this.keyPanSpeed,0),i=!0;break;case this.keys.RIGHT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(-qn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(-this.keyPanSpeed,0),i=!0;break}i&&(e.preventDefault(),this.update())}_handleTouchStartRotate(e){if(this._pointers.length===1)this._rotateStart.set(e.pageX,e.pageY);else{const i=this._getSecondPointerPosition(e),r=.5*(e.pageX+i.x),l=.5*(e.pageY+i.y);this._rotateStart.set(r,l)}}_handleTouchStartPan(e){if(this._pointers.length===1)this._panStart.set(e.pageX,e.pageY);else{const i=this._getSecondPointerPosition(e),r=.5*(e.pageX+i.x),l=.5*(e.pageY+i.y);this._panStart.set(r,l)}}_handleTouchStartDolly(e){const i=this._getSecondPointerPosition(e),r=e.pageX-i.x,l=e.pageY-i.y,c=Math.sqrt(r*r+l*l);this._dollyStart.set(0,c)}_handleTouchStartDollyPan(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enablePan&&this._handleTouchStartPan(e)}_handleTouchStartDollyRotate(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enableRotate&&this._handleTouchStartRotate(e)}_handleTouchMoveRotate(e){if(this._pointers.length==1)this._rotateEnd.set(e.pageX,e.pageY);else{const r=this._getSecondPointerPosition(e),l=.5*(e.pageX+r.x),c=.5*(e.pageY+r.y);this._rotateEnd.set(l,c)}this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const i=this.domElement;this._rotateLeft(qn*this._rotateDelta.x/i.clientHeight),this._rotateUp(qn*this._rotateDelta.y/i.clientHeight),this._rotateStart.copy(this._rotateEnd)}_handleTouchMovePan(e){if(this._pointers.length===1)this._panEnd.set(e.pageX,e.pageY);else{const i=this._getSecondPointerPosition(e),r=.5*(e.pageX+i.x),l=.5*(e.pageY+i.y);this._panEnd.set(r,l)}this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd)}_handleTouchMoveDolly(e){const i=this._getSecondPointerPosition(e),r=e.pageX-i.x,l=e.pageY-i.y,c=Math.sqrt(r*r+l*l);this._dollyEnd.set(0,c),this._dollyDelta.set(0,Math.pow(this._dollyEnd.y/this._dollyStart.y,this.zoomSpeed)),this._dollyOut(this._dollyDelta.y),this._dollyStart.copy(this._dollyEnd);const f=(e.pageX+i.x)*.5,p=(e.pageY+i.y)*.5;this._updateZoomParameters(f,p)}_handleTouchMoveDollyPan(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enablePan&&this._handleTouchMovePan(e)}_handleTouchMoveDollyRotate(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enableRotate&&this._handleTouchMoveRotate(e)}_addPointer(e){this._pointers.push(e.pointerId)}_removePointer(e){delete this._pointerPositions[e.pointerId];for(let i=0;i<this._pointers.length;i++)if(this._pointers[i]==e.pointerId){this._pointers.splice(i,1);return}}_isTrackingPointer(e){for(let i=0;i<this._pointers.length;i++)if(this._pointers[i]==e.pointerId)return!0;return!1}_trackPointer(e){let i=this._pointerPositions[e.pointerId];i===void 0&&(i=new mt,this._pointerPositions[e.pointerId]=i),i.set(e.pageX,e.pageY)}_getSecondPointerPosition(e){const i=e.pointerId===this._pointers[0]?this._pointers[1]:this._pointers[0];return this._pointerPositions[i]}_customWheelEvent(e){const i=e.deltaMode,r={clientX:e.clientX,clientY:e.clientY,deltaY:e.deltaY};switch(i){case 1:r.deltaY*=16;break;case 2:r.deltaY*=100;break}return e.ctrlKey&&!this._controlActive&&(r.deltaY*=10),r}}function c3(s){this.enabled!==!1&&(this._pointers.length===0&&(this.domElement.setPointerCapture(s.pointerId),this.domElement.ownerDocument.addEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.addEventListener("pointerup",this._onPointerUp)),!this._isTrackingPointer(s)&&(this._addPointer(s),s.pointerType==="touch"?this._onTouchStart(s):this._onMouseDown(s),this._cursorStyle==="grab"&&(this.domElement.style.cursor="grabbing")))}function u3(s){this.enabled!==!1&&(s.pointerType==="touch"?this._onTouchMove(s):this._onMouseMove(s))}function f3(s){switch(this._removePointer(s),this._pointers.length){case 0:this.domElement.releasePointerCapture(s.pointerId),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.dispatchEvent(Lx),this.state=kt.NONE,this._cursorStyle==="grab"&&(this.domElement.style.cursor="grab");break;case 1:const e=this._pointers[0],i=this._pointerPositions[e];this._onTouchStart({pointerId:e,pageX:i.x,pageY:i.y});break}}function h3(s){let e;switch(s.button){case 0:e=this.mouseButtons.LEFT;break;case 1:e=this.mouseButtons.MIDDLE;break;case 2:e=this.mouseButtons.RIGHT;break;default:e=-1}switch(e){case kr.DOLLY:if(this.enableZoom===!1)return;this._handleMouseDownDolly(s),this.state=kt.DOLLY;break;case kr.ROTATE:if(s.ctrlKey||s.metaKey||s.shiftKey){if(this.enablePan===!1)return;this._handleMouseDownPan(s),this.state=kt.PAN}else{if(this.enableRotate===!1)return;this._handleMouseDownRotate(s),this.state=kt.ROTATE}break;case kr.PAN:if(s.ctrlKey||s.metaKey||s.shiftKey){if(this.enableRotate===!1)return;this._handleMouseDownRotate(s),this.state=kt.ROTATE}else{if(this.enablePan===!1)return;this._handleMouseDownPan(s),this.state=kt.PAN}break;default:this.state=kt.NONE}this.state!==kt.NONE&&this.dispatchEvent(Lp)}function d3(s){switch(this.state){case kt.ROTATE:if(this.enableRotate===!1)return;this._handleMouseMoveRotate(s);break;case kt.DOLLY:if(this.enableZoom===!1)return;this._handleMouseMoveDolly(s);break;case kt.PAN:if(this.enablePan===!1)return;this._handleMouseMovePan(s);break}}function p3(s){this.enabled===!1||this.enableZoom===!1||this.state!==kt.NONE||(s.preventDefault(),this.dispatchEvent(Lp),this._handleMouseWheel(this._customWheelEvent(s)),this.dispatchEvent(Lx))}function m3(s){this.enabled!==!1&&this._handleKeyDown(s)}function g3(s){switch(this._trackPointer(s),this._pointers.length){case 1:switch(this.touches.ONE){case Vr.ROTATE:if(this.enableRotate===!1)return;this._handleTouchStartRotate(s),this.state=kt.TOUCH_ROTATE;break;case Vr.PAN:if(this.enablePan===!1)return;this._handleTouchStartPan(s),this.state=kt.TOUCH_PAN;break;default:this.state=kt.NONE}break;case 2:switch(this.touches.TWO){case Vr.DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchStartDollyPan(s),this.state=kt.TOUCH_DOLLY_PAN;break;case Vr.DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchStartDollyRotate(s),this.state=kt.TOUCH_DOLLY_ROTATE;break;default:this.state=kt.NONE}break;default:this.state=kt.NONE}this.state!==kt.NONE&&this.dispatchEvent(Lp)}function _3(s){switch(this._trackPointer(s),this.state){case kt.TOUCH_ROTATE:if(this.enableRotate===!1)return;this._handleTouchMoveRotate(s),this.update();break;case kt.TOUCH_PAN:if(this.enablePan===!1)return;this._handleTouchMovePan(s),this.update();break;case kt.TOUCH_DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchMoveDollyPan(s),this.update();break;case kt.TOUCH_DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchMoveDollyRotate(s),this.update();break;default:this.state=kt.NONE}}function v3(s){this.enabled!==!1&&s.preventDefault()}function x3(s){s.key==="Control"&&(this._controlActive=!0,this.domElement.getRootNode().addEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function y3(s){s.key==="Control"&&(this._controlActive=!1,this.domElement.getRootNode().removeEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function S3(s){return Math.max(0,Math.min(1,s))}function al(s){if(!s.length)return[];let e=Number.POSITIVE_INFINITY,i=Number.NEGATIVE_INFINITY;for(const l of s)l<e&&(e=l),l>i&&(i=l);const r=i-e;return r<=1e-12?s.map(()=>.5):s.map(l=>(l-e)/r)}function Nv(s){const e=S3(s),i=[{t:0,c:[33,64,154]},{t:.35,c:[35,170,211]},{t:.7,c:[255,210,95]},{t:1,c:[245,73,71]}];let r=i[0],l=i[i.length-1];for(let _=0;_<i.length-1;_+=1)if(e>=i[_].t&&e<=i[_+1].t){r=i[_],l=i[_+1];break}const c=l.t-r.t||1,f=(e-r.t)/c,p=Math.round(r.c[0]+(l.c[0]-r.c[0])*f),m=Math.round(r.c[1]+(l.c[1]-r.c[1])*f),d=Math.round(r.c[2]+(l.c[2]-r.c[2])*f);return[p/255,m/255,d/255]}function Uv(s){const e=String(s);let i=0;for(let c=0;c<e.length;c+=1)i=i*31+e.charCodeAt(c)|0;const r=(Math.abs(i)%360+360)%360,l=new Lt().setHSL(r/360,.66,.56);return[l.r,l.g,l.b]}function Ox(s){const e=s.length,i=new Float32Array(e*3);if(!e)return i;const r=s.map(d=>d[0]),l=s.map(d=>d[1]),c=s.map(d=>d[2]),f=al(r),p=al(l),m=al(c);for(let d=0;d<e;d+=1)i[d*3]=(f[d]-.5)*18,i[d*3+1]=(p[d]-.5)*18,i[d*3+2]=(m[d]-.5)*18;return i}function M3(s){const e=s.length,i=s[0]?.length??0;if(!e||!i)return new Float32Array(0);const r=new Array(i).fill(0);for(const m of s)for(let d=0;d<i;d+=1)r[d]+=m[d];for(let m=0;m<i;m+=1)r[m]/=e;const l=s.map(m=>m.map((d,_)=>d-r[_])),c=[],f=Math.min(3,i);for(let m=0;m<f;m+=1){let d=new Array(i).fill(0).map((_,v)=>Math.sin((v+1)*(m+1)*.37));for(let _=0;_<18;_+=1){const v=new Array(e).fill(0);for(let E=0;E<e;E+=1){const R=l[E];let x=0;for(let y=0;y<i;y+=1)x+=R[y]*d[y];v[E]=x}const g=new Array(i).fill(0);for(let E=0;E<e;E+=1){const R=l[E];for(let x=0;x<i;x+=1)g[x]+=R[x]*v[E]}for(const E of c){let R=0;for(let x=0;x<i;x+=1)R+=g[x]*E[x];for(let x=0;x<i;x+=1)g[x]-=R*E[x]}let M=0;for(let E=0;E<i;E+=1)M+=g[E]*g[E];if(M=Math.sqrt(M),M<=1e-10)break;d=g.map(E=>E/M)}c.push(d)}for(;c.length<3;){const m=new Array(i).fill(0);m[Math.min(c.length,i-1)]=1,c.push(m)}const p=l.map(m=>{const d=[0,0,0];for(let _=0;_<3;_+=1){let v=0;const g=c[_];for(let M=0;M<i;M+=1)v+=m[M]*g[M];d[_]=v}return d});return Ox(p)}function E3(s,e){const i=s.map(r=>[r[e]??0,r[e+1]??0,r[e+2]??0]);return Ox(i)}function b3(s){const e=s.length/3;if(!e)return{density:[],outlier:[]};const i=Math.max(3,Math.min(10,e-1)),r=new Array(e).fill(0);for(let f=0;f<e;f+=1){const p=[],m=s[f*3],d=s[f*3+1],_=s[f*3+2];for(let g=0;g<e;g+=1){if(f===g)continue;const M=m-s[g*3],E=d-s[g*3+1],R=_-s[g*3+2];p.push(Math.sqrt(M*M+E*E+R*R))}p.sort((g,M)=>g-M);const v=p.slice(0,i);r[f]=v.reduce((g,M)=>g+M,0)/v.length}const l=al(r);return{density:l.map(f=>1-f),outlier:l}}function T3(s){const e=s.length/3;if(!e)return[];if(e<5)return new Array(e).fill(0);const i=Math.max(3,Math.min(8,e-1)),r=new Array(e).fill(0);for(let g=0;g<e;g+=1){const M=[],E=s[g*3],R=s[g*3+1],x=s[g*3+2];for(let y=0;y<e;y+=1){if(g===y)continue;const T=E-s[y*3],U=R-s[y*3+1],P=x-s[y*3+2];M.push(Math.sqrt(T*T+U*U+P*P))}M.sort((y,T)=>y-T),r[g]=M[Math.min(i-1,M.length-1)]??0}const l=[...r].sort((g,M)=>g-M),c=l[Math.floor(l.length/2)]||.8,f=Math.max(.25,c*1.25),p=Math.max(4,Math.min(7,i+1)),m=Array.from({length:e},()=>[]);for(let g=0;g<e;g+=1){const M=s[g*3],E=s[g*3+1],R=s[g*3+2];for(let x=0;x<e;x+=1){if(g===x)continue;const y=M-s[x*3],T=E-s[x*3+1],U=R-s[x*3+2];Math.sqrt(y*y+T*T+U*U)<=f&&m[g].push(x)}}const d=m.map(g=>g.length>=p),_=new Array(e).fill(-1);let v=0;for(let g=0;g<e;g+=1){if(!d[g]||_[g]!==-1)continue;_[g]=v;const M=[g];for(;M.length;){const E=M.shift();for(const R of m[E])_[R]===-1&&(_[R]=v),d[R]&&!M.includes(R)&&M.push(R)}v+=1}return _}function A3({points:s,vectorDim:e,loading:i,error:r,initialQuery:l,queryLoading:c,onApplyQuery:f}){const p=K.useRef(null),m=K.useRef(null),[d,_]=K.useState("cluster"),[v,g]=K.useState("pca"),[M,E]=K.useState(0),[R,x]=K.useState(.08),[y,T]=K.useState(l),[U,P]=K.useState(null),V=K.useMemo(()=>e>0?e:s[0]?.vector?.length?s[0].vector.length:0,[s,e]),H=Math.max(0,V-3);K.useEffect(()=>{E(Q=>Math.min(Q,H))},[H]),K.useEffect(()=>{T(l)},[l]),K.useEffect(()=>{P(Q=>Q==null||Q>=s.length?null:Q)},[s.length]);const z=K.useMemo(()=>s.map(Q=>Q.vector),[s]),A=K.useMemo(()=>z.length?v==="raw_dims"?E3(z,M):M3(z):new Float32Array(0),[z,v,M]),L=K.useMemo(()=>b3(A),[A]),pe=K.useMemo(()=>T3(A),[A]),w=K.useMemo(()=>s.map((Q,de)=>{const O=Q.cluster;if(O!=null&&String(O).trim()!=="")return String(O);const j=pe[de];return j>=0?`auto-${j}`:"noise"}),[s,pe]),Y=K.useMemo(()=>s.map(Q=>Q.label!=null&&String(Q.label).trim()?String(Q.label):"unlabeled"),[s]),re=K.useMemo(()=>al(s.map(Q=>Q.similarity==null?-1:Q.similarity)),[s]),fe=K.useMemo(()=>{const Q=s.length,de=new Float32Array(Q*3);for(let O=0;O<Q;O+=1){let j=[.45,.63,.93];if(d==="cluster"){const ve=w[O];j=ve==="noise"?[.45,.45,.48]:Uv(ve)}else d==="label"?j=Y[O]==="unlabeled"?[.43,.44,.49]:Uv(Y[O]):d==="similarity"?j=s[O].similarity==null?[.35,.36,.41]:Nv(re[O]):d==="density_outlier"&&(j=Nv(L.outlier[O]??0));de[O*3]=j[0],de[O*3+1]=j[1],de[O*3+2]=j[2]}return de},[s,d,w,Y,re,L.outlier]);K.useEffect(()=>{if(!p.current)return;const Q=p.current,de=new r3({antialias:!0,alpha:!0});de.setPixelRatio(Math.min(window.devicePixelRatio||1,2)),de.setSize(Q.clientWidth,420),de.setClearColor(461586,1),Q.innerHTML="",Q.appendChild(de.domElement);const O=new jb;O.fog=new Up(461586,12,70);const j=new yi(58,Q.clientWidth/420,.01,500);j.position.set(0,0,20);const ve=new l3(j,de.domElement);ve.enableDamping=!0,ve.dampingFactor=.08,ve.screenSpacePanning=!0;const he=new Fi;he.setAttribute("position",new Yn(new Float32Array(0),3)),he.setAttribute("color",new Yn(new Float32Array(0),3));const Ne=new Sx({size:R,sizeAttenuation:!0,vertexColors:!0,transparent:!0,opacity:.95,depthWrite:!1}),ie=new eT(he,Ne);O.add(ie);const Se=new fT;Se.params.Points.threshold=.22;const Ae=new mt,Ge=()=>{const qe=Q.clientWidth;j.aspect=qe/420,j.updateProjectionMatrix(),de.setSize(qe,420)};window.addEventListener("resize",Ge);const Qe=()=>{ve.update(),de.render(O,j),m.current&&(m.current.animationHandle=window.requestAnimationFrame(Qe))};return m.current={renderer:de,camera:j,controls:ve,geometry:he,material:Ne,cloud:ie,raycaster:Se,mouse:Ae,animationHandle:window.requestAnimationFrame(Qe),resizeHandler:Ge},()=>{const qe=m.current;qe&&(window.cancelAnimationFrame(qe.animationHandle),window.removeEventListener("resize",qe.resizeHandler),qe.controls.dispose(),qe.geometry.dispose(),qe.material.dispose(),qe.renderer.dispose(),m.current=null)}},[]),K.useEffect(()=>{const Q=m.current;Q&&(Q.material.size=R,Q.geometry.setAttribute("position",new Yn(A,3)),Q.geometry.setAttribute("color",new Yn(fe,3)),Q.geometry.computeBoundingSphere(),Q.geometry.attributes.position.needsUpdate=!0,Q.geometry.attributes.color.needsUpdate=!0)},[A,fe,R]);function ee(Q){const de=m.current;if(!de)return;const O=de.renderer.domElement.getBoundingClientRect();if(!O.width||!O.height)return;de.mouse.x=(Q.clientX-O.left)/O.width*2-1,de.mouse.y=-((Q.clientY-O.top)/O.height)*2+1,de.raycaster.setFromCamera(de.mouse,de.camera);const j=de.raycaster.intersectObject(de.cloud);if(!j.length||j[0].index==null){P(null);return}P(j[0].index)}function I(Q){const de=m.current;de&&(Q==="default"&&de.camera.position.set(0,0,20),Q==="top"&&de.camera.position.set(0,24,.01),Q==="side"&&de.camera.position.set(24,0,.01),Q==="front"&&de.camera.position.set(0,.01,24),de.controls.target.set(0,0,0),de.controls.update())}const B=K.useMemo(()=>s.length?s.reduce((Q,de)=>Q+de.magnitude,0)/s.length:0,[s]),$=U!=null?s[U]??null:null;return C.jsxs("div",{style:{display:"grid",gap:10},children:[C.jsxs("div",{className:"muted",style:{display:"flex",gap:14,flexWrap:"wrap"},children:[C.jsxs("span",{children:[s.length," vectors rendered"]}),C.jsxs("span",{children:["vector dimensions: ",V||"—"]}),C.jsxs("span",{children:["avg magnitude: ",B.toFixed(4)]})]}),C.jsxs("div",{className:"toolbar",style:{marginBottom:0},children:[C.jsxs("label",{style:{display:"grid",gap:4},children:[C.jsx("span",{className:"muted",children:"Projection"}),C.jsxs("select",{"aria-label":"Embedding projection mode",value:v,onChange:Q=>g(Q.target.value),children:[C.jsx("option",{value:"pca",children:"PCA 3D (recommended)"}),C.jsx("option",{value:"raw_dims",children:"Raw dimensions (d, d+1, d+2)"})]})]}),C.jsxs("label",{style:{display:"grid",gap:4},children:[C.jsx("span",{className:"muted",children:"View"}),C.jsxs("select",{"aria-label":"Embedding color mode",value:d,onChange:Q=>_(Q.target.value),children:[C.jsx("option",{value:"cluster",children:"Cluster view"}),C.jsx("option",{value:"label",children:"Label view"}),C.jsx("option",{value:"similarity",children:"Similarity-to-query view"}),C.jsx("option",{value:"density_outlier",children:"Density / outlier view"})]})]}),C.jsxs("label",{style:{display:"grid",gap:4,minWidth:180},children:[C.jsxs("span",{className:"muted",children:["Point size: ",R.toFixed(2)]}),C.jsx("input",{"aria-label":"Embedding point size slider",type:"range",min:.03,max:.22,step:.01,value:R,onChange:Q=>x(Number(Q.target.value))})]})]}),v==="raw_dims"?C.jsxs("label",{style:{display:"grid",gap:4,minWidth:280},children:[C.jsxs("span",{className:"muted",children:["Raw dimensions: ",M,", ",Math.min(M+1,V-1),", ",Math.min(M+2,V-1)]}),C.jsx("input",{"aria-label":"Embedding dimension slider",type:"range",min:0,max:H,value:M,disabled:H<=0,onChange:Q=>E(Number(Q.target.value))})]}):C.jsx("div",{className:"muted",children:"PCA organizes correlated dimensions into stable axes for cluster exploration."}),C.jsxs("div",{className:"toolbar",style:{marginBottom:0},children:[C.jsxs("div",{className:"muted",style:{minWidth:260},children:["Active query: ",C.jsx("span",{className:"mono",children:y&&y.trim()?y.trim():"—"})]}),C.jsx("button",{onClick:()=>I("default"),children:"Default view"}),C.jsx("button",{onClick:()=>I("top"),children:"Top view"}),C.jsx("button",{onClick:()=>I("side"),children:"Side view"}),C.jsx("button",{onClick:()=>I("front"),children:"Front view"})]}),C.jsx("div",{className:"muted",children:"Legend: points are embeddings; in similarity view, brighter points are closer to the active query. Click a point to inspect details."}),r?C.jsx("div",{className:"error-banner",children:r}):null,i?C.jsx("div",{className:"muted",children:"Loading embeddings preview…"}):null,!i&&!s.length?C.jsx("div",{className:"muted",children:"No vectors available yet for this collection."}):null,C.jsx("div",{ref:p,onPointerDown:ee,style:{width:"100%",minHeight:420,border:"1px solid #263247",borderRadius:12,overflow:"hidden",background:"#070b12"}}),C.jsxs("div",{className:"panel",style:{padding:12},children:[C.jsx("h4",{style:{margin:"0 0 6px"},children:"Selected embedding"}),$?C.jsxs("div",{style:{display:"grid",gap:8},children:[C.jsxs("div",{className:"muted",children:["id: ",C.jsx("span",{className:"mono",children:String($.id)})]}),C.jsxs("div",{className:"muted",children:["label: ",$.label==null?"—":String($.label)]}),C.jsxs("div",{className:"muted",children:["cluster: ",$.cluster==null?"—":String($.cluster)]}),C.jsxs("div",{className:"muted",children:["model: ",$.embedding_model||"—"]}),C.jsxs("div",{className:"muted",children:["magnitude: ",$.magnitude.toFixed(5)]}),C.jsxs("div",{className:"muted",children:["density: ",$.density==null?"—":$.density.toFixed(5)]}),C.jsxs("div",{className:"muted",children:["outlier: ",$.outlier_score==null?"—":$.outlier_score.toFixed(5)]}),C.jsxs("div",{className:"muted",children:["similarity: ",$.similarity==null?"—":$.similarity.toFixed(5)]}),C.jsxs("div",{className:"muted",children:["path: ",$.path||"—"]}),C.jsxs("div",{className:"muted",children:["tags:"," ",$.tags==null?"—":typeof $.tags=="string"?$.tags:JSON.stringify($.tags)]}),C.jsx("pre",{className:"terminal",style:{margin:0,maxHeight:180},children:($.text??"").trim()||"—"}),$.metadata&&Object.keys($.metadata).length>0?C.jsx("pre",{className:"terminal",style:{margin:0,maxHeight:160},children:JSON.stringify($.metadata,null,2)}):null]}):C.jsx("div",{className:"muted",children:"Click a point in the 3D view to inspect its details."})]})]})}function Px({value:s,onChange:e}){return C.jsxs("details",{className:"advanced-panel",children:[C.jsx("summary",{children:"Advanced"}),C.jsxs("div",{className:"advanced-grid",children:[C.jsxs("label",{children:[C.jsx("span",{className:"muted",children:"Path filter"}),C.jsx("input",{value:s.path??"",onChange:i=>e({...s,path:i.target.value}),placeholder:"/path/to/file.txt"})]}),C.jsxs("label",{children:[C.jsx("span",{className:"muted",children:"Metric"}),C.jsxs("select",{value:(s.metric_type??"L2").toUpperCase(),onChange:i=>e({...s,metric_type:i.target.value}),children:[C.jsx("option",{value:"L2",children:"L2"}),C.jsx("option",{value:"IP",children:"IP"}),C.jsx("option",{value:"COSINE",children:"COSINE"})]})]}),C.jsxs("label",{children:[C.jsx("span",{className:"muted",children:"nprobe"}),C.jsx("input",{type:"number",min:1,value:s.nprobe??16,onChange:i=>e({...s,nprobe:Number(i.target.value)||16})})]}),C.jsxs("label",{children:[C.jsx("span",{className:"muted",children:"Hybrid fusion"}),C.jsxs("select",{value:s.hybrid_fusion??"weighted",onChange:i=>e({...s,hybrid_fusion:i.target.value}),children:[C.jsx("option",{value:"weighted",children:"weighted"}),C.jsx("option",{value:"rrf",children:"rrf"})]})]}),C.jsxs("label",{children:[C.jsx("span",{className:"muted",children:"Dense weight"}),C.jsx("input",{type:"number",min:0,max:1,step:"0.05",value:s.hybrid_dense_weight??.65,onChange:i=>e({...s,hybrid_dense_weight:Number(i.target.value)||.65})})]}),C.jsxs("label",{children:[C.jsx("span",{className:"muted",children:"Sparse weight"}),C.jsx("input",{type:"number",min:0,max:1,step:"0.05",value:s.hybrid_sparse_weight??.35,onChange:i=>e({...s,hybrid_sparse_weight:Number(i.target.value)||.35})})]}),C.jsxs("label",{children:[C.jsx("span",{className:"muted",children:"RRF k"}),C.jsx("input",{type:"number",min:1,value:s.hybrid_rrf_k??60,onChange:i=>e({...s,hybrid_rrf_k:Number(i.target.value)||60})})]}),C.jsxs("label",{className:"checkbox-label",children:[C.jsx("input",{type:"checkbox",checked:s.unique,onChange:i=>e({...s,unique:i.target.checked})}),C.jsx("span",{children:"Unique (dedupe by hash)"})]})]})]})}function R3(){const e=UM().name??"",[i,r]=K.useState(null),[l,c]=K.useState(null),[f,p]=K.useState(!0),[m,d]=K.useState({mode:"hybrid",limit:10,unique:!1,path:"",metric_type:"L2",nprobe:16,hybrid_fusion:"weighted",hybrid_dense_weight:.65,hybrid_sparse_weight:.35,hybrid_rrf_k:60}),[_,v]=K.useState(""),[g,M]=K.useState(null),[E,R]=K.useState(!1),[x,y]=K.useState([]),[T,U]=K.useState(0),[P,V]=K.useState(""),[H,z]=K.useState(null),[A,L]=K.useState(!1),[pe,w]=K.useState(!1),[Y,re]=K.useState(null),[fe,ee]=K.useState(""),[I,B]=K.useState(!1);async function $(){p(!0);try{const he=await DE(e);r(he),c(null)}catch(he){c(he instanceof Error?he.message:"Failed to fetch collection.")}finally{p(!1)}}async function Q(he){he?.useQueryLoading?w(!0):L(!0);try{const Ne=await NE(e,{limit:500,query:he?.query});y(Ne.points??[]),U(Ne.vector_dim??0),re(null),z(Ne.query_error??null),he?.query!=null&&V(he.query)}catch(Ne){const ie=Ne instanceof Error?Ne.message:"Failed to load embedding preview.";re(ie)}finally{he?.useQueryLoading?w(!1):L(!1)}}K.useEffect(()=>{$(),Q()},[e]);async function de(){if(_.trim()){R(!0);try{const he=await UE(e,{query:_,...m});M(he.results??[]),await Q({query:_,useQueryLoading:!0}),c(null)}catch(he){c(he instanceof Error?he.message:"Search failed.")}finally{R(!1)}}}async function O(){const he=fe.trim();if(he){B(!0);try{await OE(e,{text:he,chunk_size:1e3,overlap:0}),ee(""),await $(),await Q(),c(null)}catch(Ne){c(Ne instanceof Error?Ne.message:"Insert failed.")}finally{B(!1)}}}async function j(){if(confirm(`Drop collection "${e}"? This cannot be undone.`))try{await PE(e),window.location.href="/"}catch(he){c(he instanceof Error?he.message:"Drop failed.")}}const ve=K.useMemo(()=>i?i.fields.map(Ne=>Ne.name).join(", "):"",[i]);return C.jsxs("section",{style:{display:"flex",flexDirection:"column",gap:14},children:[l&&C.jsx("div",{className:"error-banner",children:l}),C.jsx("div",{className:"panel",children:C.jsxs("div",{style:{display:"flex",justifyContent:"space-between",gap:12,flexWrap:"wrap"},children:[C.jsxs("div",{children:[C.jsx("div",{className:"muted",children:C.jsx(rl,{to:"/",children:"← Back"})}),C.jsx("h2",{style:{margin:"6px 0 6px"},children:C.jsx("span",{className:"mono",children:e})}),f?C.jsx("div",{className:"muted",children:"Loading…"}):i?C.jsxs("div",{className:"muted",children:[i.num_entities," rows · fields: ",ve||"—"]}):C.jsx("div",{className:"muted",children:"Not found."})]}),C.jsxs("div",{style:{display:"flex",gap:8,alignItems:"start"},children:[C.jsx("button",{onClick:()=>{$()},disabled:f,children:"Refresh"}),C.jsx("button",{onClick:()=>{j()},disabled:f,style:{borderColor:"#7b3041"},children:"Drop"})]})]})}),C.jsxs("div",{className:"panel",children:[C.jsx("h3",{style:{marginTop:0},children:"Embeddings 3D"}),C.jsx(A3,{points:x,vectorDim:T,loading:A,error:Y,initialQuery:P||_,queryLoading:pe,onApplyQuery:async he=>{await Q({query:he,useQueryLoading:!0})}}),H?C.jsxs("div",{className:"muted",style:{marginTop:8},children:["Similarity note: ",H]}):null]}),C.jsxs("div",{className:"panel",children:[C.jsx("h3",{style:{marginTop:0},children:"Search"}),C.jsxs("div",{className:"toolbar",style:{marginBottom:12},children:[C.jsx("div",{className:"segmented",children:["dense","bm25","hybrid"].map(he=>C.jsx("button",{className:m.mode===he?"active":"",onClick:()=>d({...m,mode:he}),children:he.toUpperCase()},he))}),C.jsx("input",{value:_,onChange:he=>v(he.target.value),placeholder:"Query…",onKeyDown:he=>{he.key==="Enter"&&de()}}),C.jsx("input",{style:{width:120},value:String(m.limit),onChange:he=>d({...m,limit:Number(he.target.value)||10}),placeholder:"Limit"}),C.jsx("button",{disabled:E,onClick:()=>{de()},children:E?"Searching…":"Search"})]}),C.jsx(Px,{value:m,onChange:d}),g&&C.jsxs("div",{style:{display:"flex",flexDirection:"column",gap:10},children:[C.jsxs("div",{className:"muted",children:[g.length," results"]}),g.map(he=>C.jsxs("div",{className:"card",children:[C.jsxs("div",{className:"card-headline",children:[C.jsxs("h3",{className:"mono",title:String(he.id),children:["#",he.id]}),C.jsxs("span",{className:"pill",children:[C.jsx("span",{className:"status-dot warning"}),C.jsx("span",{children:Number.isFinite(he.distance)?he.distance.toFixed(4):"—"})]})]}),C.jsx("div",{className:"muted mono",style:{fontSize:"0.84rem"},children:he.creation_date??""}),C.jsx("pre",{className:"terminal",children:(he.text??"").trim()||"—"})]},String(he.id)))]})]}),C.jsxs("div",{className:"panel",children:[C.jsx("h3",{style:{marginTop:0},children:"Insert text"}),C.jsxs("div",{style:{display:"grid",gap:10},children:[C.jsx("textarea",{value:fe,onChange:he=>ee(he.target.value),placeholder:"Paste text to store in this collection…"}),C.jsxs("div",{style:{display:"flex",gap:10,alignItems:"center",flexWrap:"wrap"},children:[C.jsx("button",{disabled:I,onClick:()=>{O()},children:I?"Inserting…":"Insert"}),C.jsx("span",{className:"muted",children:"Uses default embedding settings unless you add options later."})]})]})]})]})}function C3(){const[s,e]=K.useState([]),[i,r]=K.useState(!0),[l,c]=K.useState(!1),[f,p]=K.useState(null),[m,d]=K.useState(""),[_,v]=K.useState(null),[g,M]=K.useState(null),[E,R]=K.useState({mode:"hybrid",limit:20,unique:!1,path:"",metric_type:"L2",nprobe:16,hybrid_fusion:"weighted",hybrid_dense_weight:.65,hybrid_sparse_weight:.35,hybrid_rrf_k:60});async function x(){try{const T=await wE(!0);e(T.collections??[]),p(null)}catch(T){p(T instanceof Error?T.message:"Failed to fetch collections.")}finally{r(!1)}}async function y(){if(m.trim()){c(!0);try{const T=await LE({query:m,...E,per_collection_limit:Math.max(E.limit,20)});v(T.results??[]),M(T.total_candidates??null),p(null)}catch(T){p(T instanceof Error?T.message:"Global search failed.")}finally{c(!1)}}}return K.useEffect(()=>{x()},[]),C.jsxs("section",{children:[f&&C.jsx("div",{className:"error-banner",children:f}),C.jsxs("div",{className:"toolbar",children:[C.jsx("input",{value:m,onChange:T=>d(T.target.value),placeholder:"Search across all collections…",onKeyDown:T=>{T.key==="Enter"&&y()}}),C.jsx("div",{className:"segmented",children:["dense","bm25","hybrid"].map(T=>C.jsx("button",{className:E.mode===T?"active":"",onClick:()=>R({...E,mode:T}),children:T.toUpperCase()},T))}),C.jsx("input",{style:{width:110},type:"number",min:1,value:E.limit,onChange:T=>R({...E,limit:Number(T.target.value)||20}),placeholder:"Limit"}),C.jsx("button",{onClick:()=>{y()},disabled:l,children:l?"Searching…":"Search"}),C.jsx("button",{onClick:()=>{x()},children:"Reload Collections"})]}),C.jsx(Px,{value:E,onChange:R}),_&&C.jsxs("div",{className:"panel",style:{marginBottom:14},children:[C.jsxs("div",{className:"card-headline",children:[C.jsx("h3",{style:{margin:0},children:"Global search results"}),C.jsxs("span",{className:"muted",children:[_.length,typeof g=="number"?` / ${g}`:""," rows"]})]}),C.jsx("div",{style:{marginTop:10,display:"flex",flexDirection:"column",gap:10},children:_.map(T=>C.jsxs("div",{className:"card",children:[C.jsxs("div",{className:"card-headline",children:[C.jsxs("h3",{className:"mono",title:String(T.id),children:["#",T.id]}),C.jsxs("div",{style:{display:"flex",gap:8,alignItems:"center"},children:[C.jsx("span",{className:"pill",children:T.collection??"unknown"}),C.jsxs("span",{className:"pill",children:[C.jsx("span",{className:"status-dot warning"}),C.jsx("span",{children:Number.isFinite(T.distance)?T.distance.toFixed(4):"—"})]})]})]}),C.jsx("div",{className:"muted mono",style:{fontSize:"0.84rem"},children:T.creation_date??""}),C.jsx("pre",{className:"terminal",children:(T.text??"").trim()||"—"}),C.jsx("div",{children:C.jsx(rl,{className:"button-link",to:`/collections/${encodeURIComponent(T.collection??"")}`,children:"Open Collection"})})]},`${T.collection??"unknown"}:${String(T.id)}:${T.distance}`))})]}),i?C.jsx("div",{className:"muted",children:"Loading collections…"}):C.jsx("div",{className:"grid",children:s.map(T=>C.jsxs("div",{className:"card",children:[C.jsxs("div",{className:"card-headline",children:[C.jsx("h3",{title:T.raw_name,children:C.jsx("span",{className:"mono",children:T.name})}),C.jsxs("span",{className:"pill",title:T.raw_name,children:[C.jsx("span",{className:"status-dot success"}),C.jsx("span",{children:typeof T.num_entities=="number"?`${T.num_entities} rows`:"—"})]})]}),C.jsxs("div",{className:"muted",children:[T.vector_dim?`dim ${T.vector_dim}`:"dim unknown"," · ",T.has_sparse?"hybrid-ready":"dense-only"]}),T.stats_error&&C.jsxs("div",{className:"muted",children:["Stats error: ",T.stats_error]}),C.jsx("div",{style:{display:"flex",gap:8,flexWrap:"wrap"},children:C.jsx(rl,{className:"button-link",to:`/collections/${encodeURIComponent(T.name)}`,children:"Open"})})]},T.raw_name))})]})}function w3(){return C.jsxs("div",{className:"app-shell",children:[C.jsxs("header",{className:"main-header",children:[C.jsx("h1",{className:"brand-title",children:"Archivist"}),C.jsxs("nav",{className:"top-nav",children:[C.jsx(vd,{className:({isActive:s})=>s?"active":"",to:"/",children:"Collections"}),C.jsx(vd,{className:({isActive:s})=>s?"active":"",to:"/backup",children:"Backup"})]})]}),C.jsxs(YM,{children:[C.jsx(tl,{path:"/",element:C.jsx(C3,{})}),C.jsx(tl,{path:"/collections/:name",element:C.jsx(R3,{})}),C.jsx(tl,{path:"/backup",element:C.jsx(XE,{})}),C.jsx(tl,{path:"*",element:C.jsx(WM,{to:"/",replace:!0})})]})]})}ZS.createRoot(document.getElementById("root")).render(C.jsx(K.StrictMode,{children:C.jsx(vE,{children:C.jsx(w3,{})})}));
