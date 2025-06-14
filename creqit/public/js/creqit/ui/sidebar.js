creqit.provide("creqit.ui");

creqit.ui.Sidebar = class Sidebar {
	constructor() {
		this.items = {};

		if (!creqit.boot.setup_complete) {
			// no sidebar if setup is not complete
			return;
		}

		this.set_all_pages();
		this.make_dom();
		this.sidebar_items = {
			public: {},
			private: {},
		};
		this.indicator_colors = [
			"green",
			"cyan",
			"blue",
			"orange",
			"yellow",
			"gray",
			"grey",
			"red",
			"pink",
			"darkgrey",
			"purple",
			"light-blue",
		];

		this.setup_pages();
	}

	make_dom() {
		this.set_default_app();
		this.wrapper = $(
			creqit.render_template("sidebar", {
				app_logo_url: creqit.boot.app_data[0].app_logo_url,
				app_title: __(creqit.boot.app_data[0].app_title),
				navbar_settings: creqit.boot.navbar_settings,
			})
		).prependTo("body");

		this.$sidebar = this.wrapper.find(".sidebar-items");
		// setTimeout(() => {
		// 	$(".navbar .container .body-sidebar-top").append(this.$sidebar);
		// 	$(" .body-sidebar-top").append(this.$sidebar);
		// }, 100);
		// $('.navbar-home').on('click', function(event) {
		// 	event.preventDefault();  // <a> etiketinin varsayılan link davranışını iptal ediyoruz
		// 	$('.body-sidebar-container').attr('style', 'display: block !important;');
		// });
		// $('.body-sidebar-container').on('mouseleave', function() {
		// 	$(this).attr('style', 'display: none !important;');
		// });
		// $('.body-sidebar-bottom .close-sidebar-link').on('click', function(event) {
		// 	event.preventDefault();  // <a> etiketinin varsayılan link davranışını iptal ediyoruz
		// 	$('.body-sidebar-container').attr('style', 'display: none !important;');
		// });
		if (this.has_access) {
			this.wrapper
				.find(".edit-sidebar-link")
				.removeClass("hidden")
				.on("click", () => {
					creqit.quick_edit("Workspace Settings");
				});
			// $(".navbar-nav")
			// .find(".nav-item")
			// .find(".edit-sidebar-link")
			// .removeClass("hidden")
			// .on("click", () => {
			// 	creqit.quick_edit("Workspace Settings");
			// });
		}

		// Sayfa yüklendiğinde, localStorage'dan 'sidebarActive' durumunu kontrol etAdd commentMore actions
		setTimeout(() => {
			const sidebar = document.querySelector('.body-sidebar-container');
			const toggleButton = document.querySelector('.sidebar-toggle-button');
		
			if (!sidebar || !toggleButton) {
				console.error('Sidebar veya toggleButton bulunamadı!');
				return;
			}
		
			// Sayfa yenilendiğinde 'active' durumunu kontrol et
			if (localStorage.getItem('sidebarActive') === 'true') {
				sidebar.classList.add('active');
				toggleButton.textContent = '<';  // Sidebar açıkken < göster
			} else {
				toggleButton.textContent = '>';  // Sidebar kapalıyken > göster
			}
		
			// Sidebar'ı açma ve kapama işlemi
			toggleButton.addEventListener('click', () => {
				sidebar.classList.toggle('active');  // active sınıfını toggle ediyoruz
		
				// Sidebar aktif durumu localStorage'a kaydediliyor
				if (sidebar.classList.contains('active')) {
					localStorage.setItem('sidebarActive', 'true');
					toggleButton.textContent = '<';  // Sidebar açıldığında < simgesini göster
				} else {
					localStorage.setItem('sidebarActive', 'false');
					toggleButton.textContent = '>';  // Sidebar kapandığında > simgesini göster
				}
			});
		}, 100); 
		
		this.setup_app_switcher();
		this.dropdownListUser();
		let user_avatar = creqit.avatar(creqit.session.user, "avatar-icon");
		const userEmail = creqit.session.user_email;
		const displayedEmail = userEmail.length > 18 ? userEmail.substring(0, 18) + "..." : userEmail;

		$(`<div class="sidebar-user-icon">${user_avatar}</div>
			<div class="sidebar-user-info">
				<div class="sidebar-user-info-fullname">${creqit.session.user_fullname}</div>
				<div class="sidebar-user-info-email" title="${userEmail}">${displayedEmail}</div>
			</div>`).appendTo(".sidebar-user");
	}

	dropdownListUser(){
		// Belirli bir sınıfa sahip li elemanlarını bulup gizle
		if(creqit.session.user !== "Administrator"){
			setTimeout(() => {
				const dropdownMenu = document.getElementById("toolbar-user");
				const buttons = dropdownMenu.querySelectorAll(".dropdown-item");			  
				for (let i = 0; i < 8; i++) {
					if(i == 0 || i == 3 || i == 5 || i == 7){
						continue;
					}
					if (buttons[i]) {
						buttons[i].style.display = 'none'; 
					}
				}
			}, 100);
		}
		//////creqit.v1.sevval
	}

	set_all_pages() {
		this.sidebar_pages = creqit.boot.sidebar_pages;
		this.all_pages = this.sidebar_pages.pages;
		this.has_access = this.sidebar_pages.has_access;
		this.has_create_access = this.sidebar_pages.has_create_access;
	}

	set_default_app() {
		// sort apps based on # of workspaces
		creqit.boot.app_data.sort((a, b) => (a.workspaces.length < b.workspaces.length ? 1 : -1));
		creqit.current_app = creqit.boot.app_data[0].app_name;
	}

	setup_app_switcher() {
		let app_switcher_menu = $(".app-switcher-menu");

		$(".app-switcher-dropdown").on("click", () => {
			app_switcher_menu.toggleClass("hidden");
		});

		// hover out of the sidebar
		 this.wrapper.find(".body-sidebar").on("mouseleave", () => {
			$("#toolbar-user").removeClass("show");
		// 	app_switcher_menu.addClass("hidden");

		// 	// hide any expanded menus as they leave a blank space in the sidebar
		// 	this.wrapper.find(".drop-icon[data-state='opened'").click();
		 });

		creqit.boot.app_data_map = {};
		this.add_private_app(app_switcher_menu);

		for (var app of creqit.boot.app_data) {
			creqit.boot.app_data_map[app.app_name] = app;
			if (app.workspaces?.length) {
				this.add_app_item(app, app_switcher_menu);
			}
		}
		this.add_website_select(app_switcher_menu);
		this.setup_select_app(app_switcher_menu);
	}

	add_app_item(app, app_switcher_menu) {//#UPDATES --sevval img>src>rul
		$(`<div class="app-item" data-app-name="${app.app_name}"
			data-app-route="${app.app_route}">
			<a>
				<div class="sidebar-item-icon">
					<img
						class="app-logo"
						src="/assets/creqit/images/creqit_mini.svg" 
						alt="${__("App Logo")}"
					>
				</div>
				<span class="app-item-title">${app.app_title}</span>
			</a>
		</div>`).appendTo(app_switcher_menu);
	}

	add_private_app(app_switcher_menu) {
		let private_pages = this.all_pages.filter((p) => p.public === 0);
		if (private_pages.length === 0) return;

		const app = {
			app_name: "private",
			app_title: __("My Workspaces"),
			app_route: "/app/private",
			app_logo_url: "/assets/creqit/images/creqit_mini.svg",//#UPDATES --sevval img>src>rul
			workspaces: private_pages,
		};

		creqit.boot.app_data_map["private"] = app;
		$(`<div class="divider"></div>`).prependTo(app_switcher_menu);
		$(`<div class="app-item" data-app-name="${app.app_name}"
			data-app-route="${app.app_route}">
			<a>
				<div class="sidebar-item-icon">
					<img
						class="app-logo"
						src="${app.app_logo_url}"
						alt="${__("App Logo")}"
					>
				</div>
				<span class="app-item-title">${app.app_title}</span>
			</a>
		</div>`).prependTo(app_switcher_menu);
	}

	setup_select_app(app_switcher_menu) {
		app_switcher_menu.find(".app-item").on("click", (e) => {
			let item = $(e.delegateTarget);
			let route = item.attr("data-app-route");
			app_switcher_menu.toggleClass("hidden");

			if (route.startsWith("/app/private")) {
				this.set_current_app("private");
				let ws = Object.values(creqit.workspace_map).find((ws) => ws.public === 0);
				route += "/" + creqit.router.slug(ws.title);
				creqit.set_route(route);
			} else if (route.startsWith("/app")) {
				creqit.set_route(route);
				this.set_current_app(item.attr("data-app-name"));
			} else {
				// new page
				window.open(route);
			}
		});
	}

	set_current_app(app) {
		if (!app) {
			console.warn("set_current_app: app not defined");
			return;
		}
		let app_data = creqit.boot.app_data_map[app] || creqit.boot.app_data_map["creqit"];

		this.wrapper
			.find(".app-switcher-dropdown .sidebar-item-icon img")
			.attr("src", app_data.app_logo_url);
		this.wrapper.find(".app-switcher-dropdown .sidebar-item-label").html(app_data.app_title);

		$(".navbar-brand .app-logo").attr("src", app_data.app_logo_url);

		if (creqit.current_app === app) return;
		creqit.current_app = app;

		// re-render the sidebar
		this.make_sidebar();
	}

	add_website_select(app_switcher_menu) {
		$(`<div class="divider"></div>`).appendTo(app_switcher_menu);
		this.add_app_item(
			{
				app_name: "website",
				app_title: __("Website"),
				app_route: "/",
				app_logo_url: "/assets/creqit/images/web.svg",
			},
			app_switcher_menu
		);
	}

	setup_pages() {
		this.set_all_pages();

		this.all_pages.forEach((page) => {
			page.is_editable = !page.public || this.has_access;
			if (typeof page.content == "string") {
				page.content = JSON.parse(page.content);
			}
		});		

		if (this.all_pages) {
			creqit.workspaces = {};
			creqit.workspace_list = [];
			creqit.workspace_map = {};
			for (let page of this.all_pages) {
				creqit.workspaces[creqit.router.slug(page.name)] = {
					name: page.name,
					public: page.public,
				};
				if (!page.app && page.module) {
					page.app = creqit.boot.module_app[creqit.slug(page.module)];
				}
				creqit.workspace_map[page.name] = page;
				creqit.workspace_list.push(page);
			}
			this.make_sidebar();
		}
	}

	make_sidebar() {
		if (this.wrapper.find(".standard-sidebar-section")[0]) {
			this.wrapper.find(".standard-sidebar-section").remove();
		}

		let app_workspaces = creqit.boot.app_data_map[creqit.current_app || "creqit"].workspaces;

		let parent_pages = this.all_pages.filter((p) => !p.parent_page).uniqBy((p) => p.name);
		if (creqit.current_app === "private") {
			parent_pages = parent_pages.filter((p) => !p.public);
		} else {
			parent_pages = parent_pages.filter((p) => p.public && app_workspaces.includes(p.name));
		}

		this.build_sidebar_section("All", parent_pages);

		// Scroll sidebar to selected page if it is not in viewport.
		this.wrapper.find(".selected").length &&
			!creqit.dom.is_element_in_viewport(this.wrapper.find(".selected")) &&
			this.wrapper.find(".selected")[0].scrollIntoView();

		this.setup_sorting();
	}

	build_sidebar_section(title, root_pages) {
		let sidebar_section = $(
			`<div class="standard-sidebar-section nested-container" data-title="${title}"></div>`
		);

		this.prepare_sidebar(root_pages, sidebar_section, this.wrapper.find(".sidebar-items"));

		if (Object.keys(root_pages).length === 0) {
			sidebar_section.addClass("hidden");
		}

		$(".item-anchor").on("click", () => {
			$(".list-sidebar.hidden-xs.hidden-sm").removeClass("opened");
			//$(".close-sidebar").css("display", "none");
			$("body").css("overflow", "auto");
		});

		if (
			sidebar_section.find(".sidebar-item-container").length &&
			sidebar_section.find("> [item-is-hidden='0']").length == 0
		) {
			sidebar_section.addClass("hidden show-in-edit-mode");
		}
		sidebar_section.find(".sidebar-child-item .sidebar-item-icon").addClass('hidden'); //child itemların ikonları gizlendi
	}

	prepare_sidebar(items, child_container, item_container) {
		let last_item = null;
		for (let item of items) {
			if (item.public && last_item && !last_item.public) {
				$(`<div class="divider"></div>`).appendTo(child_container);
			}

			// visibility not explicitly set to 0
			if (item.visibility !== 0) {
				this.append_item(item, child_container);
			}
			last_item = item;
		}
		child_container.appendTo(item_container);
	}

	append_item(item, container) {
		let is_current_page = false;

		item.selected = is_current_page;

		if (is_current_page) {
			this.current_page = { name: item.name, public: item.public };
		}

		let $item_container = this.sidebar_item_container(item);
		let sidebar_control = $item_container.find(".sidebar-item-control");

		let child_items = this.all_pages.filter(
			(page) => page.parent_page == item.name || page.parent_page == item.title
		);
		if (child_items.length > 0) {
			$item_container.find(".item-anchor").attr("href", "#"); //child olan paretpage açılmasın diye
			let child_container = $item_container.find(".sidebar-child-item");
			child_container.addClass("hidden"); //dropdownların kapalı gelmesi için açıldı yorum satırıydı //sevval
			this.prepare_sidebar(child_items, child_container, $item_container);

			let currentPath = window.location.pathname;
			if (currentPath.startsWith('/app/query-report')) {	
				currentPath = '/app/raporlar';
			}//creqit.v1.sevval
			$item_container.find('a.item-anchor').each(function() {
				let anchorHref = $(this).attr('href');
				if (anchorHref && anchorHref.startsWith('/app/query-report')) {
					anchorHref = '/app/raporlar';
				}//creqit.v1.sevval
				if (anchorHref && anchorHref === currentPath) {
					child_container.removeClass('hidden');
					//$item_container.addClass('-active');
					// if ($item_container.find('-active') ) {
					// 	console.log("sdfsdf")
					// 	$item_container.find('.sidebar-item-icon svg').css("stroke", "var(--creqit-lavender-blue-300)"); // İkonu kırmızıya boyuyoruz
					// }//creqit.v1.sevval
					if (!$item_container.attr('item-parent')) {
						$item_container.addClass('-active');
						// let $nextItem = $item_container.find('.-active .standard-sidebar-item').first();
						// if ($nextItem.length) {
						// 	$nextItem.find('.standard-sidebar-item').css('background-color', '#f0f0f0');
						// }//creqit.v1.sevval
					}
					
				}
			});
			
		}
		if (child_items.length < 0) {
			//let child_container = $item_container.find(".sidebar-child-item");
			child_container.addClass("hidden");
			//this.prepare_sidebar(child_items, child_container, $item_container);
		}

		$item_container.appendTo(container);
		this.sidebar_items[item.public ? "public" : "private"][item.name] = $item_container;

		if ($item_container.parent().hasClass("hidden") && is_current_page) {
			$item_container.parent().toggleClass("hidden");
		}

		this.add_toggle_children(item, sidebar_control, $item_container);

		if (child_items.length > 0) {
			$item_container.find(".drop-icon").first().addClass("show-in-edit-mode");
		}
		//$item_container.click(() => {
			//this.url(item);
		//});

	}
	//bu fonksiyon sidebar üzerinde aktif sayfa durumu kontrolu için eklendi
	// url(item) {		
	// 	setTimeout(() => {
	// 	  const currentPath = window.location.pathname;	  
	// 	  let path;
	// 	  if (item.public) {
	// 		path = "/app/" + creqit.router.slug(item.name);
	// 	  } else {
	// 		path = "/app/private/" + creqit.router.slug(item.name.split("-")[0]);
	// 	  }
	//   	  document.querySelectorAll(".sidebar-item-container").forEach(div => {
	// 		div.classList.remove("-active");
	// 	  });
	  
	// 	  if (currentPath === path) {
	  
	// 		document.querySelectorAll(".sidebar-item-container").forEach(div => {
	// 		  let link = div.querySelector("a");
	// 		  if (link) {
	// 			const linkPath = link.getAttribute("href");
	// 			if (linkPath === path) {
	// 			  div.classList.add("-active");
	// 			}
	// 		  }
	// 		});
	// 	  }
	// 	}, 100);
	//   }
	  

	sidebar_item_container(item) {

		let currentPath = window.location.pathname;
		//sidebar rapor aktifliği için eklendi <<creqit.v1.sevval
		if (currentPath.startsWith('/app/query-report')) {	
			currentPath = '/app/raporlar';
		}//creqit.v1.sevval			
		item.indicator_color =
			item.indicator_color || this.indicator_colors[Math.floor(Math.random() * 12)];
		let path;
		if (item.type === "Link") {
			if (item.link_type === "Report") {
				path = creqit.utils.generate_route({
					type: item.link_type,
					name: item.link_to,
					is_query_report: item.report.report_type === "Query Report",
					report_ref_doctype: item.report.ref_doctype,
				});
			} else {
				path = creqit.utils.generate_route({ type: item.link_type, name: item.link_to });
			}
		} else if (item.type === "URL") {
			path = item.external_link;
		} else {
			if (item.public) {
				path = "/app/" + creqit.router.slug(item.name);
			} else {
				path = "/app/private/" + creqit.router.slug(item.name.split("-")[0]);
			}
		}
		return $(`
			<div
				class="sidebar-item-container ${item.is_editable ? "is-draggable" : ""} ${currentPath == path ? "-active" : ""}"
				item-parent="${item.parent_page}"
				item-name="${item.name}"
				item-title="${item.title}"
				item-public="${item.public || 0}"
				item-is-hidden="${item.is_hidden || 0}"
			>
				<div class="standard-sidebar-item ${item.selected ? "selected" : ""}">
					<a
						href="${path}"
						target="${item.type === "URL" ? "_blank" : ""}"
						class="item-anchor ${item.is_editable ? "" : "block-click"}" title="${__(item.title)}"
					>
						<span class="sidebar-item-icon" item-icon=${item.icon || "folder-normal"}>
							${
								item.public || item.icon
									? creqit.utils.icon(item.icon || "folder-normal", "md")
									: `<span class="indicator ${item.indicator_color}"></span>`
							}
						</span>
						 <span class="sidebar-item-label">${__(item.title)}<span>
					</a>
					<div class="sidebar-item-control"></div>
				</div>
				<div class="sidebar-child-item nested-container"></div>
			</div>
		`);
	}

	add_toggle_children(item, sidebar_control, item_container) {
		let drop_icon = "es-creqit-line-down";
		if (
			this.current_page &&
			item_container.find(`[item-name="${this.current_page.name}"]`).length
		) {
			drop_icon = "small-up";
		}

		let $child_item_section = item_container.find(".sidebar-child-item");
		let $drop_icon = $(`<button class="btn-reset drop-icon hidden">`)
			.html(creqit.utils.icon(drop_icon, "sm"))
			.appendTo(sidebar_control);

		if (
			this.all_pages.some(
				(e) =>
					(e.parent_page == item.title || e.parent_page == item.name) &&
					(e.is_hidden == 0 || !this.is_read_only)
			)
		) {
			$drop_icon.removeClass("hidden");
		}
		$drop_icon.on("click", () => {
			toggleChildItems($drop_icon, $child_item_section);
		});
		item_container.on("click", function (e) {
			e.stopPropagation();  
			if ($(e.target).closest('.drop-icon').length) {
				return;
			}
			toggleChildItems($drop_icon, $child_item_section);
		});
		//tıklama olayı tüm satırdan alınsın
		function toggleChildItems($drop_icon, $child_item_section)  {
			let opened = $drop_icon.find("use").attr("href") === "#es-creqit-line-down";

			if (!opened) {
				$drop_icon.attr("data-state", "closed").find("use").attr("href", "#es-creqit-line-down");
			} else {
				$drop_icon.attr("data-state", "opened").find("use").attr("href", "#es-creqit-line-up");
			}
			``;
			$child_item_section.toggleClass("hidden");

			//alt öğe içerisindeki alt öğelerin kapalı gelmesi için //sevval
			$child_item_section.children(".sidebar-item-container").each(function () {
				$(this).find(".sidebar-child-item").addClass("hidden"); // İç içe olan alt öğeleri gizli tut
			});
		}
	}

	setup_sorting() {
		if (!this.has_access) return;
	
		for (let container of this.$sidebar.find(".nested-container")) {
			Sortable.create(container, {
				group: "sidebar-items",
				fitler: ".divider",
				onEnd: () => {
					let sidebar_items = [];
					for (let container of this.$sidebar.find(".nested-container")) {
						for (let item of $(container).children()) {
							let parent = "";
							if ($(item).parent().hasClass("sidebar-child-item")) {
								parent = $(item)
									.parent()
									.closest(".sidebar-item-container")
									.attr("item-name");
							}

							sidebar_items.push({
								name: item.getAttribute("item-name"),
								parent: parent,
							});
						}
					}
					creqit.xcall(
						"creqit.desk.doctype.workspace_settings.workspace_settings.set_sequence",
						{
							sidebar_items: sidebar_items,
						}
					);
				},
			});
		}
	}

	reload() {
		return creqit.workspace.get_pages().then((r) => {
			creqit.boot.sidebar_pages = r;
			this.setup_pages();
		});
	}
};
