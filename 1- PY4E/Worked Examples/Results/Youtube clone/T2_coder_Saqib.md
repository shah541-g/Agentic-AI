<!-- Task T2: Write the complete HTML5 and CSS3 code (using Tailwind CSS via CDN for styling) within a single file to create the YouTube clone frontend, including sidebar, navbar, video grid, and responsive design. -->

```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Clone</title>
    <!-- Tailwind CSS via CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        ytblack: '#0f0f0f',
                        ytsurface: '#212121',
                        ytsurfacehover: '#272727',
                        ytborder: '#3f3f3f',
                        yttextprimary: '#f1f1f1',
                        yttextsecondary: '#aaa',
                        ytsidebar: '#0f0f0f',
                        ytblue: '#3ea6ff',
                        ytred: '#ff0000'
                    }
                }
            }
        }
    </script>
    <!-- FontAwesome for Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* Custom Scrollbars */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: #aaa;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #fff;
        }
        body {
            background-color: #0f0f0f;
            color: #f1f1f1;
            font-family: "Roboto", Arial, sans-serif;
        }
    </style>
</head>
<body class="bg-ytblack text-yttextprimary antialiased overflow-x-hidden">

    <!-- TOP NAVIGATION BAR -->
    <header class="fixed top-0 left-0 w-full h-14 bg-ytblack z-50 flex items-center justify-between px-4 border-b border-transparent">
        <!-- Left: Hamburger & Logo -->
        <div class="flex items-center space-x-4">
            <button id="menu-btn" class="p-2 hover:bg-ytsurfacehover rounded-full text-yttextprimary transition">
                <i class="fa-solid fa-bars text-lg"></i>
            </button>
            <a href="#" class="flex items-center space-x-1">
                <div class="bg-ytred text-white px-2 py-1 rounded-xl flex items-center justify-center">
                    <i class="fa-solid fa-play text-xs"></i>
                </div>
                <span class="font-bold text-xl tracking-tighter">YouTube</span>
            </a>
        </div>

        <!-- Center: Search Bar & Mic -->
        <div class="flex items-center flex-1 max-w-2xl mx-4 justify-center">
            <div class="flex items-center w-full">
                <div class="flex items-center w-full bg-[#121212] border border-ytborder rounded-l-full px-4 py-2 focus-within:border-ytblue">
                    <input type="text" placeholder="Search" class="w-full bg-transparent outline-none text-yttextprimary placeholder-yttextsecondary text-sm">
                </div>
                <button class="bg-ytsurfacehover border border-l-0 border-ytborder px-6 py-2 rounded-r-full hover:bg-[#303030] text-yttextprimary transition">
                    <i class="fa-solid fa-magnifying-glass"></i>
                </button>
            </div>
            <button class="ml-3 p-2.5 bg-ytsurface hover:bg-ytsurfacehover rounded-full text-yttextprimary transition">
                <i class="fa-solid fa-microphone"></i>
            </button>
        </div>

        <!-- Right: Actions & Avatar -->
        <div class="flex items-center space-x-3">
            <button class="p-2.5 hover:bg-ytsurfacehover rounded-full text-yttextprimary transition relative">
                <i class="fa-solid fa-video text-lg"></i>
            </button>
            <button class="p-2.5 hover:bg-ytsurfacehover rounded-full text-yttextprimary transition relative">
                <span class="absolute top-1.5 right-1.5 bg-ytred text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full">9+</span>
                <i class="fa-regular fa-bell text-lg"></i>
            </button>
            <div class="w-8 h-8 rounded-full overflow-hidden bg-gray-500 cursor-pointer">
                <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&h=100&fit=crop&crop=faces" alt="Avatar" class="w-full h-full object-cover">
            </div>
        </div>
    </header>

    <!-- MAIN APP WRAPPER -->
    <div class="flex pt-14 min-h-screen">

        <!-- NAVIGATION SIDEBAR -->
        <aside id="sidebar" class="fixed left-0 top-14 bottom-0 w-64 bg-ytblack px-3 py-3 overflow-y-auto z-40 transition-all duration-200 hidden md:block">
            <!-- Group 1 -->
            <div class="space-y-1 pb-3 border-b border-ytborder">
                <a href="#" class="flex items-center space-x-6 px-3 py-2.5 rounded-xl bg-ytsurface hover:bg-ytsurfacehover font-medium text-sm">
                    <i class="fa-solid fa-house w-6 text-center text-lg"></i>
                    <span>Home</span>
                </a>
                <a href="#" class="flex items-center space-x-6 px-3 py-2.5 rounded-xl hover:bg-ytsurfacehover font-normal text-sm">
                    <i class="fa-solid fa-bolt w-6 text-center text-lg"></i>
                    <span>Shorts</span>
                </a>
                <a href="#" class="flex items-center space-x-6 px-3 py-2.5 rounded-xl hover:bg-ytsurfacehover font-normal text-sm">
                    <i class="fa-solid fa-clapperboard w-6 text-center text-lg"></i>
                    <span>Subscriptions</span>
                </a>
            </div>

            <!-- Group 2 (Library) -->
            <div class="space-y-1 py-3 border-b border-ytborder">
                <div class="px-3 py-1 font-semibold text-sm flex items-center justify-between">
                    <span>You</span>
                    <i class="fa-solid fa-chevron-right text-xs"></i>
                </div>
                <a href="#" class="flex items-center space-x-6 px-3 py-2.5 rounded-xl hover:bg-ytsurfacehover text-sm">
                    <i class="fa-solid fa-user-shield w-6 text-center"></i>
                    <span>Your Channel</span>
                </a>
                <a href="#" class="flex items-center space-x-6 px-3 py-2.5 rounded-xl hover:bg-ytsurfacehover text-sm">
                    <i class="fa-solid fa-clock-rotate-left w-6 text-center"></i>
                    <span>History</span>
                </a>
                <a href="#" class="flex items-center space-x-6 px-3 py-2.5 rounded-xl hover:bg-ytsurfacehover text-sm">
                    <i class="fa-solid fa-play w-6 text-center"></i>
                    <span>Your Videos</span>
                </a>
                <a href="#" class="flex items-center space-x-6 px-3 py-2.5 rounded-xl hover:bg-ytsurfacehover text-sm">
                    <i class="fa-solid fa-clock w-6 text-center"></i>
                    <span>Watch Later</span>
                </a>
                <a href="#" class="flex items-center space-x-6 px-3 py-2.5 rounded-xl hover:bg-ytsurfacehover text-sm">
                    <i class="fa-solid fa-thumbs-up w-6 text-center"></i>
                    <span>Liked Videos</span>
                </a>
            </div>

            <!-- Group 3 (Subscriptions) -->
            <div class="space-y-1 py-3 border-b border-ytborder">
                <div class="px-3 py-1 font-semibold text-sm text-yttextsecondary">Subscriptions</div>
                <a href="#" class="flex items-center space-x-4 px-3 py-2 rounded-xl hover:bg-ytsurfacehover text-sm">
                    <img src="https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=50&h=50&fit=crop" class="w-6 h-6 rounded-full object-cover">
                    <span class="truncate">Tech Insider</span>
                </a>
                <a href="#" class="flex items-center space-x-4 px-3 py-2 rounded-xl hover:bg-ytsurfacehover text-sm">
                    <img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=50&h=50&fit=crop" class="w-6 h-6 rounded-full object-cover">
                    <span class="truncate">Design Basics</span>
                </a>
                <a href="#" class="flex items-center space-x-4 px-3 py-2 rounded-xl hover:bg-ytsurfacehover text-sm">
                    <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=50&h=50&fit=crop" class="w-6 h-6 rounded-full object-cover">
                    <span class="truncate">Code Academy</span>
                </a>
            </div>

            <!-- Footer Meta -->
            <div class="py-3 px-3 text-[11px] text-yttextsecondary space-y-2">
                <p>About Press Copyright Contact us Creators Advertise Developers</p>
                <p>Terms Privacy Policy & Safety How YouTube works Test new features</p>
                <p class="text-ytborder mt-3">&copy; 2026 Google LLC</p>
            </div>
        </aside>

        <!-- MAIN CONTENT AREA -->
        <main id="main-content" class="flex-1 md:ml-64 p-4 transition-all duration-200">
            
            <!-- Category Chips Bar -->
            <div class="sticky top-14 bg-ytblack z-30 pb-3 pt-1 flex items-center space-x-3 overflow-x-auto no-scrollbar whitespace-nowrap">
                <button class="bg-yttextprimary text-ytblack px-3 py-1.5 rounded-lg text-sm font-medium transition">All</button>
                <button class="bg-ytsurface hover:bg-ytsurfacehover text-yttextprimary px-3 py-1.5 rounded-lg text-sm font-medium transition">Gaming</button>
                <button class="bg-ytsurface hover:bg-ytsurfacehover text-yttextprimary px-3 py-1.5 rounded-lg text-sm font-medium transition">Music</button>
                <button class="bg-ytsurface hover:bg-ytsurfacehover text-yttextprimary px-3 py-1.5 rounded-lg text-sm font-medium transition">Live</button>
                <button class="bg-ytsurface hover:bg-ytsurfacehover text-yttextprimary px-3 py-1.5 rounded-lg text-sm font-medium transition">Podcasts</button>
                <button class="bg-ytsurface hover:bg-ytsurfacehover text-yttextprimary px-3 py-1.5 rounded-lg text-sm font-medium transition">Programming</button>
                <button class="bg-ytsurface hover:bg-ytsurfacehover text-yttextprimary px-3 py-1.5 rounded-lg text-sm font-medium transition">UX/UI</button>
                <button class="bg-ytsurface hover:bg-ytsurfacehover text-yttextprimary px-3 py-1.5 rounded-lg text-sm font-medium transition">Cooking</button>
                <button class="bg-ytsurface hover:bg-ytsurfacehover text-yttextprimary px-3 py-1.5 rounded-lg text-sm font-medium transition">Gadgets</button>
                <button class="bg-ytsurface hover:bg-ytsurfacehover text-yttextprimary px-3 py-1.5 rounded-lg text-sm font-medium transition">Python</button>
            </div>

            <!-- Video Feed Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mt-4">
                
                <!-- Video Card Item -->
                <div class="flex flex-col cursor-pointer group">
                    <div class="relative w-full aspect-video rounded-xl overflow-hidden bg-ytsurface">
                        <img src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&h=338&fit=crop" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" alt="Thumbnail">
                        <span class="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded font-semibold">14:22</span>
                    </div>
                    <div class="flex mt-3 space-x-3">
                        <div class="w-9 h-9 rounded-full bg-gray-600 flex-shrink-0 overflow-hidden">
                            <img src="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop" class="w-full h-full object-cover">
                        </div>
                        <div class="flex flex-col flex-1">
                            <h3 class="font-semibold text-sm leading-snug line-clamp-2 text-yttextprimary">Building a Fullstack YouTube Clone using Tailwind CSS & Modern Web Design Systems</h3>
                            <span class="text-xs text-yttextsecondary mt-1 flex items-center">
                                Code Creators <i class="fa-solid fa-circle-check text-[10px] ml-1"></i>
                            </span>
                            <span class="text-xs text-yttextsecondary">125K views &bull; 2 days ago</span>
                        </div>
                    </div>
                </div>

                <!-- Video Card Item -->
                <div class="flex flex-col cursor-pointer group">
                    <div class="relative w-full aspect-video rounded-xl overflow-hidden bg-ytsurface">
                        <img src="https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600&h=338&fit=crop" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" alt="Thumbnail">
                        <span class="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded font-semibold">45:10</span>
                    </div>
                    <div class="flex mt-3 space-x-3">
                        <div class="w-9 h-9 rounded-full bg-gray-600 flex-shrink-0 overflow-hidden">
                            <img src="https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=100&h=100&fit=crop" class="w-full h-full object-cover">
                        </div>
                        <div class="flex flex-col flex-1">
                            <h3 class="font-semibold text-sm leading-snug line-clamp-2 text-yttextprimary">The Ultimate Cyberpunk RPG Gameplay Walkthrough - 4K 60FPS Max Settings</h3>
                            <span class="text-xs text-yttextsecondary mt-1 flex items-center">
                                Pixel Gaming <i class="fa-solid fa-circle-check text-[10px] ml-1"></i>
                            </span>
                            <span class="text-xs text-yttextsecondary">1.2M views &bull; 1 week ago</span>
                        </div>
                    </div>
                </div>

                <!-- Video Card Item -->
                <div class="flex flex-col cursor-pointer group">
                    <div class="relative w-full aspect-video rounded-xl overflow-hidden bg-ytsurface">
                        <img src="https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=600&h=338&fit=crop" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" alt="Thumbnail">
                        <span class="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded font-semibold">08:05</span>
                    </div>
                    <div class="flex mt-3 space-x-3">
                        <div class="w-9 h-9 rounded-full bg-gray-600 flex-shrink-0 overflow-hidden">
                            <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop" class="w-full h-full object-cover">
                        </div>
                        <div class="flex flex-col flex-1">
                            <h3 class="font-semibold text-sm leading-snug line-clamp-2 text-yttextprimary">Top 10 CSS Tricks You Didn't Know Existed in 2026</h3>
                            <span class="text-xs text-yttextsecondary mt-1 flex items-center">
                                Web Dev Simplified
                            </span>
                            <span class="text-xs text-yttextsecondary">45K views &bull; 5 hours ago</span>
                        </div>
                    </div>
                </div>

                <!-- Video Card Item -->
                <div class="flex flex-col cursor-pointer group">
                    <div class="relative w-full aspect-video rounded-xl overflow-hidden bg-ytsurface">
                        <img src="https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=600&h=338&fit=crop" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" alt="Thumbnail">
                        <span class="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded font-semibold">22:15</span>
                    </div>
                    <div class="flex mt-3 space-x-3">
                        <div class="w-9 h-9 rounded-full bg-gray-600 flex-shrink-0 overflow-hidden">
                            <img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop" class="w-full h-full object-cover">
                        </div>
                        <div class="flex flex-col flex-1">
                            <h3 class="font-semibold text-sm leading-snug line-clamp-2 text-yttextprimary">Clean Architecture in Node.js & Enterprise Best Practices</h3>
                            <span class="text-xs text-yttextsecondary mt-1 flex items-center">
                                Tech Lead <i class="fa-solid fa-circle-check text-[10px] ml-1"></i>
                            </span>
                            <span class="text-xs text-yttextsecondary">88K views &bull; 3 days ago</span>
                        </div>
                    </div>
                </div>

                <!-- Video Card Item -->
                <div class="flex flex-col cursor-pointer group">
                    <div class="relative w-full aspect-video rounded-xl overflow-hidden bg-ytsurface">
                        <img src="https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&h=338&fit=crop" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" alt="Thumbnail">
                        <span class="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded font-semibold">10:01</span>
                    </div>
                    <div class="flex mt-3 space-x-3">
                        <div class="w-9 h-9 rounded-full bg-gray-600 flex-shrink-0 overflow-hidden">
                            <img src="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop" class="w-full h-full object-cover">
                        </div>
                        <div class="flex flex-col flex-1">
                            <h3 class="font-semibold text-sm leading-snug line-clamp-2 text-yttextprimary">Understanding Matrix Math & Vectors in Game Development</h3>
                            <span class="text-xs text-yttextsecondary mt-1 flex items-center">
                                Code Creators <i class="fa-solid fa-circle-check text-[10px] ml-1"></i>
                            </span>
                            <span class="text-xs text-yttextsecondary">32K views &bull; 1 day ago</span>
                        </div>
                    </div>
                </div>

                <!-- Video Card Item -->
                <div class="flex flex-col cursor-pointer group">
                    <div class="relative w-full aspect-video rounded-xl overflow-hidden bg-ytsurface">
                        <img src="https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=600&h=338&fit=crop" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" alt="Thumbnail">
                        <span class="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded font-semibold">03:45</span>
                    </div>
                    <div class="flex mt-3 space-x-3">
                        <div class="w-9 h-9 rounded-full bg-gray-600 flex-shrink-0 overflow-hidden">
                            <img src="https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=100&h=100&fit=crop" class="w-full h-full object-cover">
                        </div>
                        <div class="flex flex-col flex-1">
                            <h3 class="font-semibold text-sm leading-snug line-clamp-2 text-yttextprimary">Lo-Fi Coding Beats to Relax & Study To (Live Stream)</h3>
                            <span class="text-xs text-yttextsecondary mt-1 flex items-center">
                                ChillHop Music <i class="fa-solid fa-circle-check text-[10px] ml-1"></i>
                            </span>
                            <span class="text-xs text-yttextsecondary">3.4K watching now</span>
                        </div>
                    </div>
                </div>

                <!-- Video Card Item -->
                <div class="flex flex-col cursor-pointer group">
                    <div class="relative w-full aspect-video rounded-xl overflow-hidden bg-ytsurface">
                        <img src="https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=600&h=338&fit=crop" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" alt="Thumbnail">
                        <span class="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded font-semibold">18:20</span>
                    </div>
                    <div class="flex mt-3 space-x-3">
                        <div class="w-9 h-9 rounded-full bg-gray-600 flex-shrink-0 overflow-hidden">
                            <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop" class="w-full h-full object-cover">
                        </div>
                        <div class="flex flex-col flex-1">
                            <h3 class="font-semibold text-sm leading-snug line-clamp-2 text-yttextprimary">Inside the World's Most Advanced AI Research Facility</h3>
                            <span class="text-xs text-yttextsecondary mt-1 flex items-center">
                                Future Tech
                            </span>
                            <span class="text-xs text-yttextsecondary">510K views &bull; 4 days ago</span>
                        </div>
                    </div>
                </div>

                <!-- Video Card Item -->
                <div class="flex flex-col cursor-pointer group">
                    <div class="relative w-full aspect-video rounded-xl overflow-hidden bg-ytsurface">
                        <img src="https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&h=338&fit=crop" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" alt="Thumbnail">
                        <span class="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded font-semibold">12:00</span>
                    </div>
                    <div class="flex mt-3 space-x-3">
                        <div class="w-9 h-9 rounded-full bg-gray-600 flex-shrink-0 overflow-hidden">
                            <img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop" class="w-full h-full object-cover">
                        </div>
                        <div class="flex flex-col flex-1">
                            <h3 class="font-semibold text-sm leading-snug line-clamp-2 text-yttextprimary">Custom Mechanical Keyboard Building Guide for Programmers</h3>
                            <span class="text-xs text-yttextsecondary mt-1 flex items-center">
                                Switch Craft
                            </span>
                            <span class="text-xs text-yttextsecondary">99K views &bull; 6 days ago</span>
                        </div>
                    </div>
                </div>

            </div>
        </main>
    </div>

    <!-- Simple JS toggling behavior for responsive sidebar -->
    <script>
        const menuBtn = document.getElementById('menu-btn');
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('main-content');

        menuBtn.addEventListener('click', () => {
            if (sidebar.classList.contains('md:block')) {
                sidebar.classList.remove('md:block');
                sidebar.classList.add('hidden');
                mainContent.classList.remove('md:ml-64');
                mainContent.classList.add('md:ml-0');
            } else {
                sidebar.classList.remove('hidden');
                sidebar.classList.add('md:block');
                mainContent.classList.remove('md:ml-0');
                mainContent.classList.add('md:ml-64');
            }
        });
    </script>
</body>
</html>
```

### Usage Note
1. Save the code into a single file named `index.html`.
2. Open the file directly in any modern web browser (Chrome, Firefox, Edge, Safari) to view the fully responsive YouTube frontend interface complete with a dark mode layout, navigation header, scrollable category filter bar, collapsible sidebar, and responsive video grid using Tailwind CSS via CDN.
