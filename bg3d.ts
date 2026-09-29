// 3D Animated Background using Three.js with Fragment Explosion & Dual-Theme Animations
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('bg-canvas') as HTMLCanvasElement;
    if (!canvas || !(window as any).THREE) {
        const login = document.getElementById('loginScreen');
        if (login) login.classList.remove('login-hidden');
        const hint = document.getElementById('clickHint');
        if (hint) hint.classList.add('hint-hidden');
        return;
    }

    const THREE = (window as any).THREE;

    // Scene setup
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0f172a, 0.002);

    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 30;

    const renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        alpha: true,
        antialias: true
    });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(window.innerWidth, window.innerHeight);

    // ==========================================
    // LOGIN LOGO (Explosion)
    // ==========================================
    const logoGroup = new THREE.Group();
    scene.add(logoGroup);

    const geometry = new THREE.IcosahedronGeometry(10, 1);
    
    const material = new THREE.MeshBasicMaterial({
        color: 0x3b82f6,
        wireframe: true,
        transparent: true,
        opacity: 0.5
    });
    
    const coreMaterial = new THREE.MeshPhongMaterial({
        color: 0x1e3a8a,
        flatShading: true,
        shininess: 100,
        transparent: true,
        opacity: 1
    });

    const wireframeMesh = new THREE.Mesh(geometry, material);
    const coreMesh = new THREE.Mesh(geometry, coreMaterial);
    coreMesh.scale.set(0.95, 0.95, 0.95);

    logoGroup.add(wireframeMesh);
    logoGroup.add(coreMesh);

    // ==========================================
    // DARK MODE: DATA STREAM
    // ==========================================
    const streamGeometry = new THREE.BufferGeometry();
    const streamCount = 600;
    const streamPos = new Float32Array(streamCount * 3);
    const streamSpeeds = new Float32Array(streamCount);

    for(let i = 0; i < streamCount; i++) {
        streamPos[i*3] = (Math.random() - 0.5) * 120; 
        streamPos[i*3+1] = (Math.random() - 0.5) * 100; 
        streamPos[i*3+2] = (Math.random() - 0.5) * 60 - 20; 
        streamSpeeds[i] = Math.random() * 0.1 + 0.02; 
    }

    streamGeometry.setAttribute('position', new THREE.BufferAttribute(streamPos, 3));
    streamGeometry.setAttribute('speed', new THREE.BufferAttribute(streamSpeeds, 1));

    const streamMaterial = new THREE.PointsMaterial({
        size: 0.15,
        color: 0x60a5fa,
        transparent: true,
        opacity: 0.3, 
        blending: THREE.AdditiveBlending
    });

    const streamMesh = new THREE.Points(streamGeometry, streamMaterial);
    scene.add(streamMesh);

    // ==========================================
    // LIGHT MODE: FLOATING RINGS/BUBBLES
    // ==========================================
    const lightModeGroup = new THREE.Group();
    scene.add(lightModeGroup);
    
    const bubbleCount = 40;
    const bubbles: any[] = [];
    
    const bubbleGeo = new THREE.RingGeometry(0.8, 1, 32);
    // Use NormalBlending so it shows up on white backgrounds!
    const bubbleMat = new THREE.MeshBasicMaterial({
        color: 0x2563eb,
        transparent: true,
        opacity: 0.15,
        side: THREE.DoubleSide,
        blending: THREE.NormalBlending
    });

    for(let i=0; i<bubbleCount; i++) {
        const mesh = new THREE.Mesh(bubbleGeo, bubbleMat);
        mesh.position.set(
            (Math.random() - 0.5) * 80,
            (Math.random() - 0.5) * 80,
            (Math.random() - 0.5) * 40 - 10
        );
        
        const scale = Math.random() * 3 + 1;
        mesh.scale.set(scale, scale, scale);
        
        mesh.rotation.set(
            Math.random() * Math.PI,
            Math.random() * Math.PI,
            0
        );
        
        const floatSpeed = Math.random() * 0.03 + 0.01;
        const rotSpeedX = (Math.random() - 0.5) * 0.02;
        const rotSpeedY = (Math.random() - 0.5) * 0.02;

        lightModeGroup.add(mesh);
        bubbles.push({ mesh, floatSpeed, rotSpeedX, rotSpeedY });
    }

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x3b82f6, 2, 50);
    pointLight.position.set(10, 10, 10);
    scene.add(pointLight);

    const pointLight2 = new THREE.PointLight(0x8b5cf6, 2, 50);
    pointLight2.position.set(-10, -10, 10);
    scene.add(pointLight2);

    // Explosion Variables
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let isExploded = false;
    let explosionProgress = 0;
    const fragments: any[] = []; 

    // Animation Loop
    const clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);
        
        const elapsedTime = clock.getElapsedTime();

        // Dark Mode: Data Stream Animation
        if (streamMesh.visible) {
            const positions = streamGeometry.attributes.position.array as Float32Array;
            const speeds = streamGeometry.attributes.speed.array as Float32Array;
            for(let i = 0; i < streamCount; i++) {
                positions[i*3+1] -= speeds[i]; // move down
                if (positions[i*3+1] < -50) {
                    positions[i*3+1] = 50; // wrap to top
                }
            }
            streamGeometry.attributes.position.needsUpdate = true;
        }

        // Light Mode: Bubbles Animation
        if (lightModeGroup.visible) {
            for(let i=0; i<bubbles.length; i++) {
                const b = bubbles[i];
                b.mesh.position.y += b.floatSpeed;
                b.mesh.rotation.x += b.rotSpeedX;
                b.mesh.rotation.y += b.rotSpeedY;
                
                if(b.mesh.position.y > 40) {
                    b.mesh.position.y = -40;
                }
            }
        }


        if (!isExploded) {
            // Normal Idle Animation for Logo
            logoGroup.rotation.y = elapsedTime * 0.2;
            logoGroup.rotation.x = elapsedTime * 0.1;
            logoGroup.position.y = Math.sin(elapsedTime * 0.5) * 2;

            // Hover effect check
            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects([coreMesh, wireframeMesh]);
            if (intersects.length > 0) {
                document.body.style.cursor = 'pointer';
                coreMesh.scale.setScalar(1.05);
                wireframeMesh.scale.setScalar(1.1);
            } else {
                document.body.style.cursor = 'default';
                coreMesh.scale.setScalar(0.95);
                wireframeMesh.scale.setScalar(1);
            }
        } else {
            // Explosion Animation for Logo
            explosionProgress += 0.015;

            for (let i = 0; i < fragments.length; i++) {
                const frag = fragments[i];
                frag.mesh.position.add(frag.velocity);
                frag.velocity.multiplyScalar(0.96); 
                frag.mesh.rotation.x += frag.rotationSpeed.x;
                frag.mesh.rotation.y += frag.rotationSpeed.y;
                frag.mesh.rotation.z += frag.rotationSpeed.z;
                
                if (frag.mesh.material.opacity > 0) {
                    frag.mesh.material.opacity -= 0.005;
                }
            }
        }

        // Camera gentle sway
        camera.position.x += (mouseX * 5 - camera.position.x) * 0.02;
        camera.position.y += (-mouseY * 5 - camera.position.y) * 0.02;
        camera.lookAt(scene.position);

        renderer.render(scene, camera);
    }

    // Mouse tracking
    let mouseX = 0;
    let mouseY = 0;
    
    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX / window.innerWidth) * 2 - 1;
        mouseY = (event.clientY / window.innerHeight) * 2 - 1;
        
        if (!isExploded) {
            mouse.x = mouseX;
            mouse.y = -mouseY;
        }
    });

    // Click handler for explosion
    window.addEventListener('click', () => {
        if (isExploded) return;
        // Zjednodušeno: kliknutí kamkoliv spustí explozi a ukáže login.
        // Toto řeší problém, kdy WebGL selže a uživatel nevidí model.
        triggerExplosion();
    });

    function triggerExplosion() {
        isExploded = true;
        document.body.style.cursor = 'default';
        logoGroup.visible = false;
        
        const fragmentGeometries = [
            new THREE.TetrahedronGeometry(1.5),
            new THREE.BoxGeometry(1, 1, 1),
            new THREE.IcosahedronGeometry(1)
        ];
        
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        // Ensure fragment materials use NormalBlending for light theme visibility
        const colors = isDark ? [0x3b82f6, 0x60a5fa, 0x1e3a8a, 0x93c5fd] : [0x2563eb, 0x1d4ed8, 0x1e40af, 0x3b82f6];

        for (let i = 0; i < 70; i++) {
            const geo = fragmentGeometries[Math.floor(Math.random() * fragmentGeometries.length)];
            const isWireframe = Math.random() > 0.5;
            
            const mat = new THREE.MeshPhongMaterial({
                color: colors[Math.floor(Math.random() * colors.length)],
                wireframe: isWireframe,
                flatShading: true,
                transparent: true,
                opacity: 1,
                blending: isDark ? THREE.AdditiveBlending : THREE.NormalBlending
            });
            
            const mesh = new THREE.Mesh(geo, mat);
            mesh.position.set((Math.random() - 0.5) * 5, (Math.random() - 0.5) * 5, (Math.random() - 0.5) * 5);
            scene.add(mesh);
            
            const speed = Math.random() * 2 + 1;
            const velocity = new THREE.Vector3((Math.random() - 0.5) * speed, (Math.random() - 0.5) * speed, (Math.random() - 0.5) * speed);
            const rotationSpeed = new THREE.Vector3((Math.random() - 0.5) * 0.4, (Math.random() - 0.5) * 0.4, (Math.random() - 0.5) * 0.4);
            
            fragments.push({ mesh, velocity, rotationSpeed });
        }

        const hint = document.getElementById('clickHint');
        if(hint) hint.classList.add('hint-hidden');

        setTimeout(() => {
            const loginScreen = document.getElementById('loginScreen');
            if (loginScreen) {
                loginScreen.classList.remove('login-hidden');
            }
        }, 2500);
    }

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    function updateThemeColors() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if(isDark) {
            scene.fog.color.setHex(0x0f172a);
            coreMaterial.color.setHex(0x1e3a8a);
            material.color.setHex(0x3b82f6);
            
            // Show stream, hide bubbles
            streamMesh.visible = true;
            lightModeGroup.visible = false;
        } else {
            scene.fog.color.setHex(0xf8fafc);
            coreMaterial.color.setHex(0x60a5fa);
            material.color.setHex(0x2563eb);
            
            // Show bubbles, hide stream
            streamMesh.visible = false;
            lightModeGroup.visible = true;
        }
    }
    
    updateThemeColors();
    const observer = new MutationObserver(updateThemeColors);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

    animate();
});
